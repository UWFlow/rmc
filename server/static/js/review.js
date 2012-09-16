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

    initialize: function(attributes) {
      if (!attributes || !attributes.professor) {
        this.set('professor', _.clone(this.defaults.professor));
      }
      if (!attributes || !attributes.course) {
        this.set('course', _.clone(this.defaults.course));
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
      'click .add-review': 'showReview',
      'click .save-review': 'saveReview',
      'change .comments,.prof-select': 'allowSave'
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

      this.model.on('change', this.allowSave, this);
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
    },

    saveReview: function() {
      // TODO(david): This should just be an underscore template
      // TODO(david): Should initially be in this state if user had review
      // TODO(david): This should actually save to backend and show a saving...
      //     spinner in the meanwhile
      this.$('.save-review')
        .removeClass('btn-primary')
        .addClass('btn-success')
        .prop('disabled', true)
        .html('<i class="icon-ok"></i> Saved.');
    },

    allowSave: function() {
      this.$('.save-review')
        .removeClass('btn-success')
        .addClass('btn-primary')
        .prop('disabled', false)
        .html('<i class="icon-save"></i> Save!');
    }
  });

  return {
    UserReviewModel: UserReviewModel,
    UserReviewView: UserReviewView
  };
});
