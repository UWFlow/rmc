define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string'],
function(Backbone, $, _, _s) {

  var CourseModel = Backbone.Model.extend({
  });

  var CourseCardView = Backbone.View.extend({
    tagName: 'li',
    className: 'course-card',

    initialize: function(options) {
      this.courseModel = options.courseModel;
    },

    render: function() {
      this.$el.html(_s.sprintf('<li class="course">%s</li>', this.courseModel.get('code')));
      return this;
    }
  });

  return {
    CourseModel: CourseModel,
    CourseCardView: CourseCardView
  }
});
