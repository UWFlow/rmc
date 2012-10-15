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
      this.userCourse = options.userCourse;
    },

    render: function() {
      this.$el.html(this.template(this.userCourse.toJSON()));

      if (this.courseModel) {
        this.userCourseView = new _user_course.UserCourseView({
          userCourse: this.userCourse,
          courseModel: this.courseModel
        });

        this.$('.user-course-placeholder').html(
            this.userCourseView.render().el);
        this.$('.user-course-container').fadeIn();
      }
      return this;
    },

    events: {
      'click .add-course-placeholder': 'onCourseSelect'
    },

    onCourseSelect: function() {
      // FIXME(david): Completely remove any old UserCourse stuff
      // FIXME(david): don't hardcode
      var courseId = 'cs115';
      this.userCourse.set('course_id', courseId);

      var courseDeferred = $.getJSON('/api/courses/' + courseId);
      var userCourseDeferred = $.getJSON('/api/user/course?404ok',
          { course_id: courseId });

      var deferredHandlers = _.bind(function(courseArgs, userCourseArgs) {
        var courseData = courseArgs[0];
        var userCourseData = userCourseArgs[0];

        _course.CourseCollection.addToCache(courseData.course_objs);
        _prof.ProfCollection.addToCache(courseData.professor_objs);

        var courseObj = courseData.course_objs[0];
        this.courseModel = _course.CourseCollection.getFromCache(courseObj.id);

        // TODO(david): Handle the case of user changing their existing
        //     favourite course to a course they haven't taken before (should
        //     show empty review, but currently they will just be editing their
        //     old review). This is not done yet because this involves
        //     significant duplication of default UserCourse data on the client.
        //     One solution: for old (non-onboarding) users, only allow
        //     selecting from courses they've taken.
        if (userCourseData.status !== 404) {
          this.userCourse = new _user_course.UserCourse(userCourseData);
        }

        this.render();
      }, this);

      $.when(courseDeferred, userCourseDeferred).then(deferredHandlers);
    }

  });

  return {
    AddFavCourseView: AddFavCourseView
  };
});
