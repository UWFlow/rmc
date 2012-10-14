define(
['rmc_backbone', 'ext/jquery', 'ext/jqueryui', 'ext/underscore',
'ext/underscore.string', 'ext/select2', 'ext/bootstrap', 'user_course',
'course', 'prof'],
function(RmcBackbone, $, _jqueryui, _, _s, _select2, _bootstrap, _user_course,
    _course, _prof) {

  var AddFavCourseView = RmcBackbone.View.extend({
    template: _.template($('#add-fav-course-tpl').html()),
    className: 'add-fav-course',

    initialize: function(options) {
      this.favCourse = options.favCourse;  // FavCourse is a UserCourse model
    },

    render: function() {
      this.$el.html(this.template(this.favCourse.toJSON()));
      return this;
    },

    events: {
      'click .add-course-placeholder': 'onCourseSelect'
    },

    onCourseSelect: function() {
      // FIXME(david): Completely remove any old UserCourse stuff
      // FIXME(david): don't hardcode
      this.favCourse.set('course_id', 'cs135');

      $.getJSON('/api/courses/cs135', _.bind(function(data) {
        _course.CourseCollection.addToCache(data.course_objs);
        _prof.ProfCollection.addToCache(data.professor_objs);

        var courseObj = data.course_objs[0];
        var courseModel = _course.CourseCollection.getFromCache(courseObj.id);

        this.favCourseView = new _user_course.UserCourseView({
          userCourse: this.favCourse,
          courseModel: courseModel
        });

        this.$('.user-course-placeholder').html(this.favCourseView.render().el);
        this.$('.user-course-container').fadeIn();
      }, this));
    }

  });

  return {
    AddFavCourseView: AddFavCourseView
  };
});
