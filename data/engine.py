import json
import logging
import os
import math
import datetime
from shutil import rmtree

from pyspark import SparkContext
from pyspark.mllib.recommendation import ALS, MatrixFactorizationModel

import mongoengine
import rmc.models as m
import rmc.shared.constants as c

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_PARAMS = {
    'num_courses': 3,
    'num_iterations': 20,
    'reg_param': 0.1,
    'rank': 12,
}


class RecommendationEngine:
    def __init__(self, sc):
        """Initialize the engine given a spark context"""
        log.info('Starting up the Recommendation Engine: ')
        self.sc = sc

    def load_data(self):
        # Model must be already trained and saved to recommendation folder
        model_path = os.path.join(os.path.dirname(__file__),
                                  '%s/trained_model' % c.RECOMMENDATION_DIR)
        self.model = MatrixFactorizationModel.load(self.sc, model_path)

        user_path = os.path.join(os.path.dirname(__file__),
                                 '%s/user.json' % c.RECOMMENDATION_DIR)
        with open(user_path, 'r') as f:
            self.user_lookup = json.load(f)

        course_path = os.path.join(os.path.dirname(__file__),
                                   '%s/course.json' % c.RECOMMENDATION_DIR)
        with open(course_path, 'r') as f:
            self.course_lookup = json.load(f)

    def __prepare_data(self):
        log.info('Preparing user data')
        user_lookup = dict((str(user.id), index) for index, user in
                           enumerate(m.User.objects))
        user_path = os.path.join(os.path.dirname(__file__),
                                 '%s/user.json' % c.RECOMMENDATION_DIR)
        with open(user_path, 'w') as f:
            json.dump(user_lookup, f)

        log.info('Preparing course data')
        course_lookup = dict((course.id, index) for index, course in
                             enumerate(m.Course.objects))
        course_path = os.path.join(os.path.dirname(__file__),
                                   '%s/course.json' % c.RECOMMENDATION_DIR)
        with open(course_path, 'w') as f:
            json.dump(course_lookup, f)

        return user_lookup, course_lookup

    def train(self):
        "Train the model with new data and write to file"
        user_lookup, course_lookup = self.__prepare_data()

        # send list of (user_id, course_id, rating) triples to the ML algorithm
        log.info('Loading ratings data')
        ratings_RDD_raw = self.sc.parallelize(m.UserCourse.objects)
        self.ratings_RDD = (ratings_RDD_raw
                            .filter(lambda ratings:
                                    ratings.course_review.interest is not None)
                            .map(lambda ratings:
                                 (user_lookup[str(ratings.user_id)],
                                  course_lookup[ratings.course_id],
                                  float(ratings.course_review.interest)))
                            ).cache()
        training_error, test_error = self._report_error(self.ratings_RDD)

        log.info('Training model')
        model = ALS.train(self.ratings_RDD,
                          _PARAMS['rank'],
                          _PARAMS['num_iterations'],
                          _PARAMS['reg_param'])
        log.info('Model trained!')
        model_path = os.path.join(os.path.dirname(__file__),
                                  '%s/trained_model' % c.RECOMMENDATION_DIR)
        if os.path.isdir(model_path):
            rmtree(model_path)
        model.save(self.sc, model_path)

        self._report_metrics(num_courses=self.ratings_RDD.count(),
                             training_error=training_error,
                             test_error=test_error)

    def _report_metrics(self, **kw):
        metrics = {}
        for key, value in kw.iteritems():
            metrics[key] = value
        now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        metrics_file_path = os.path.join(os.path.dirname(__file__),
                                         '%s/metrics/%s.json' %
                                         (c.RECOMMENDATION_DIR, now))
        with open(metrics_file_path, 'w') as f:
            json.dump(metrics, f)

    def _report_error(self, data_set):
        training_set, test_set = data_set.randomSplit([7, 3], seed=0L)
        model = ALS.train(training_set,
                          _PARAMS['rank'],
                          _PARAMS['num_iterations'],
                          _PARAMS['reg_param'])
        training_error = self._get_rsme(model, training_set)
        test_error = self._get_rsme(model, test_set)
        return training_error, test_error

    def _get_rsme(self, model, data_set):
        test_for_predict_RDD = data_set.map(lambda x: (x[0], x[1]))
        predictions = model.predictAll(test_for_predict_RDD).map(
            lambda r: ((r[0], r[1]), r[2]))
        rates_and_preds = data_set.map(
            lambda r: ((int(r[0]), int(r[1])), float(r[2]))).join(predictions)
        return math.sqrt(rates_and_preds.map(
            lambda r: (r[1][0] - r[1][1]) ** 2).mean())

    def recommend_user(self, user_id, n):
        """Recommend top n courses to the user provided"""
        if user_id:
            user = self.user_lookup.get(user_id, None)
            if user is None:
                raise Exception('User %s is not in the database' % user_id)
        else:
            raise Exception('Please provide a user id')

        user_courses = m.UserCourse.objects(user_id=user_id)
        user_course_ids = [uc.course_id for uc in user_courses]
        uc_with_rating = len([uc for uc in user_courses
                             if uc.course_review.interest is not None])
        if uc_with_rating:
            top_ratings = self.model.recommendProducts(
                    user,
                    n + len(user_course_ids))
            inv_course_lookup = {v: k for k, v in self.course_lookup.items()}
            top_course_ids = [rating[1] for rating in top_ratings]
            top_courses = [inv_course_lookup[course_id]
                           for course_id in top_course_ids]
        else:
            log.info('User %s has not rated any courses, \
                recommending most liked courses' % user_id)
            top_courses = [course.id for course in
                           get_most_liked_courses(n + len(user_course_ids))]
        recommended_courses = [course for course in top_courses
                               if course not in user_course_ids]
        recommended_courses = recommended_courses[:min(n, len(top_courses))]
        log.info('Top %s recommendations for user \"%s\":\n%s'
                 % (n, user_id, '\n'.join(recommended_courses)))
        return recommended_courses


def get_most_liked_courses(n):
    """Get the top n courses with the most likes and ratings"""
    input = {
        'sort_mode': 'interesting',
        'count': n
    }
    return m.Course.search(params=input)[0]


def save_recommendations_to_mongo():
    log.info('Saving recommendations to database...')
    for user in m.User.objects:
        try:
            user.recommended_courses = engine.recommend_user(
                str(user.id),
                _PARAMS['num_courses'])
            user.save()
        except Exception as e:
            log.error(e)

if __name__ == '__main__':
    mongoengine.connect(c.MONGO_DB_RMC)
    sc = SparkContext()
    sc.setCheckpointDir('data/recommendation/checkpoint/')
    engine = RecommendationEngine(sc)
    engine.train()
    engine.load_data()
    save_recommendations_to_mongo()
