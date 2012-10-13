define(
['rmc_backbone', 'ext/jquery', 'ext/jqueryui', 'ext/underscore',
'ext/underscore.string', 'ext/select2', 'ext/bootstrap', 'user_course'],
function(RmcBackbone, $, _jqueryui, _, _s, _select2, _bootstrap, _user_course) {

  var AddFavCourseView = RmcBackbone.View.extend({
    template: _.template($('#add-fav-course-tpl').html()),
    className: 'add-fav-course',

    initialize: function(options) {
      this.favCourse = options.favCourse;  // FavCourse is a UserCourse model
    },

    render: function() {
      this.$el.html(this.template(this.favCourse.toJSON()));
      return this;
    }
  });

  return {
    AddFavCourseView: AddFavCourseView
  };
});
