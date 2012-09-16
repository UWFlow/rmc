define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'ext/select2', 'ext/autosize'],
function(Backbone, $, _, _s, ratings, select2) {

  // TODO(david): May want to refactor to just a UserCourse model
  var UserReviewModel = Backbone.Model.extend({
    defaults: {
      term: 'Spring 2012',
      professor: {
        name: 'Larry Smith',
        passion: null,
        clarity: 0.3,
        overall: 0.4,
        comments: 'Professor was Larry Smith. Enough said.'
      },
      course: {
        easiness: 0.1,
        interest: 0.7,
        overall: 5,
        comments: 'blha blahb lbha lbahbla blhabl blah balhb balh balh'
      }
    },

    // TODO(david): If I designed this better, all this code below might not be
    //     necessary
    getRatingObj: function(name) {
      var prof = this.get('professor');
      if (_.has(prof, name)) {
        return prof;
      }

      var course = this.get('course');
      if (_.has(course, name)) {
        return course;
      }
    },

    getRating: function(name) {
      return this.getRatingObj(name)[name];
    },

    setRating: function(name, value) {
      // TODO(david): Alternatively, don't nest objects in backbone models
      var obj = this.getRatingObj(name);
      obj[name] = value;
      return this.set(name, obj);
    }
  });

  var UserReviewView = Backbone.View.extend({
    events: {
      'change .prof-select': 'showReview',
      'click .add-review': 'showReview'
    },

    initialize: function(options) {
    },

    render: function() {
      this.$el.html(
        _.template($('#review-tpl').html(), this.model.toJSON()));

      // TODO(david): Make this prettier and conform to our styles
      // TODO(david): Allow adding a prof
      this.$('.prof-select').select2({
      });

      this.$('.comments')
        .autosize()
        .css('resize', 'none');

      return this;
    },

    showReview: function() {
      this.$('.review-details').slideDown();
      this.$('.add-review').fadeOut('fast');
    }
  });

  return {
    UserReviewModel: UserReviewModel,
    UserReviewView: UserReviewView
  };
});
