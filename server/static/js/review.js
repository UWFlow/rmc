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
        clarity: null,
        overall: null,
        comments: 'Professor was Larry Smith. Enough said.'
      },
      course: {
        easiness: null,
        interest: null,
        overall: null,
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
      var obj = this.getRatingObj(name);
      obj[name] = value;
      this.trigger('change');
      return this.set(name, obj);
    }
  });

  var UserReviewView = Backbone.View.extend({
    events: {
      'change .prof-select': 'showReview',
      'click .add-review': 'showReview'
    },

    initialize: function(options) {
      this.courseRatingsView = new ratings.RatingsView({
        userReviewModel: this.model,
        userOnly: true,
        ratings: new ratings.RatingCollection(
            [{ name: 'interest' }, { name: 'easiness' }])
      });
      this.profRatingsView = new ratings.RatingsView({
        userReviewModel: this.model,
        userOnly: true,
        ratings: new ratings.RatingCollection(
            [{ name: 'clarity' }, { name: 'passion' }])
      });
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

      this.$('.course-ratings-placeholder').replaceWith(
          this.courseRatingsView.render().el);
      this.$('.prof-ratings-placeholder').replaceWith(
          this.profRatingsView.render().el);

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
