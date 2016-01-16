define(
['rmc_backbone', 'ext/underscore', 'ext/jquery', 'course'],
function(RmcBackbone, _, $, _course) {

  var RecommendationModel = RmcBackbone.Model.extend({
    defaults: {
      'course_ids': []
    },
    
    referenceFields: {
      'courses': ['course_ids', _course.CourseCollection]
    }
  });


  var RecommendationView = RmcBackbone.View.extend({
    className: 'recommendation',
    
    initialize: function(options) {
      this.recommendationModel = options.recommendationModel;
      this.courses = this.recommendationModel.get('courses');
      this.courseCollectionView = new _course.CourseCollectionView({
        courses: this.courses,
        canShowAddReview: pageData.ownProfile
      });
      this.courseCollectionView.bind('addedToShortlist',
                                     this.removeCourse, this);
      this.template =_.template($('#recommendation-tpl').html());
      
    },

    removeCourse: function(course_id) {
      this.courses.remove(_course.CourseCollection.getFromCache(course_id));
      this.render();
      this.trigger('addedToShortlist', course_id);
    },

    render: function(options) {
      this.num_courses = this.courses.length;
      this.$el.html(this.template({'num_courses': this.num_courses}));
      this.$el.find('.course-collection-placeholder').replaceWith(
          this.courseCollectionView.render().el);
      return this;
    }
  });

  return {
    RecommendationView: RecommendationView,
    RecommendationModel: RecommendationModel
  };
});
