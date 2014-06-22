require(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ratings', 'util', 'review',
 'tips', 'sign_in'],
function(backbone, $, _, ratings, util, _review, tips) {
  var overallRating = new ratings.RatingCollection(
    pageData.profRatings.filter(function(r) {
      return r.name !== 'overall' && r.name !== 'easiness'
    }));

  var overallRatingsView = new ratings.RatingsView({
    ratings: overallRating,
    subject: 'professor'
  });

  var kittenNum = util.getHashCode(pageData.profName) % pageData.NUM_KITTENS;
  $('.prof-info-placeholder').replaceWith(
    _.template($('#prof-inner-tpl').html())({
      'kittenNum': kittenNum
    })
  );

  $('.career-rating-placeholder').html(overallRatingsView.render().el);

  var ratingBoxView = new ratings.RatingBoxView({
    model: new ratings.RatingModel (pageData.profRatings.filter(function(r) {
      return r.name === 'overall'
    })[0])
  });

  $('#rating-box-container').html(ratingBoxView.render().el);

  $('.prof-courses-placeholder').replaceWith(
      _.template($('#prof-courses-tpl').html())({
          'courses': window.pageData.profCourses
      })
  );

  _.each(window.pageData.tipObjsByCourse, function(course_reviews) {
    if (course_reviews.reviews.length === 0) {
      return;
    }
    var tipsCollection = new _review.ReviewCollection(course_reviews.reviews);
    var fullCourse = _.find(window.pageData.profCoursesFull,
        function(course) {
          return course.id.toUpperCase() === course_reviews.course_id;
        }
    );
    var tipsView = new tips.ExpandableTipsView({
      reviews: tipsCollection,
      numShown: 3,
      course: fullCourse
    });
    var rendered_prof_review = $(tipsView.render().el);
    $('#tips-collection-container').replaceWith(rendered_prof_review.add(
        $('<div id=tips-collection-container></div>')));
  });

  $(document.body).trigger('pageScriptComplete');
});
