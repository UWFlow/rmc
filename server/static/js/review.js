define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'ext/select2', 'ext/autosize'],
function(Backbone, $, _, _s, ratings, select2) {

  // TODO(david): May want to refactor to just a UserCourse model
  // TODO(david): Refactor to use sub-models for reviews
  var UserReviewModel = Backbone.Model.extend({
    // TODO(mack): use undefined rather than null
    defaults: {
      id: null,
      term_id: '2012_05',
      course_id: null,
      professor_id: null,
      professor_review: {
        passion: null,
        clarity: null,
        comment: ''
      },
      course_review: {
        easiness: null,
        interest: null,
        comment: ''
      }
    },

    url: function() {
      return '/api/user/course';
    },

    initialize: function(attributes) {
      if (!attributes || !attributes.professor_review) {
        this.set('professor_review', _.clone(this.defaults.professor_review));
      }
      if (!attributes || !attributes.course_review) {
        this.set('course_review', _.clone(this.defaults.course_review));
      }
    },

    // TODO(david): If I designed this better, all this code below might not be
    //     necessary
    _getRatingObj: function(name) {
      var prof = this.get('professor_review');
      if (_.has(prof, name)) {
        return [prof, 'professor_review'];
      }

      var course = this.get('course_review');
      if (_.has(course, name)) {
        return [course, 'course_review'];
      }
    },

    getRating: function(name) {
      return this._getRatingObj(name)[0][name];
    },

    setRating: function(name, value) {
      var obj = this._getRatingObj(name);
      var attrs = obj[0];
      var objName = obj[1];
      attrs[name] = value;
      this.set(objName, attrs);
      this.trigger('change');
      return this;
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
      this.userReviewModel = options.userReviewModel;
      this.courseModel = options.courseModel;

      this.courseRatingsView = new ratings.RatingsView({
        userReviewModel: this.userReviewModel,
        userOnly: true,
        ratings: new ratings.RatingCollection(
            [{ name: 'interest' }, { name: 'easiness' }])
      });
      this.profRatingsView = new ratings.RatingsView({
        userReviewModel: this.userReviewModel,
        userOnly: true,
        ratings: new ratings.RatingCollection(
            [{ name: 'clarity' }, { name: 'passion' }])
      });

      this.userReviewModel.on('change', this.allowSave, this);
    },

    render: function() {
      var context = _.extend(this.userReviewModel.toJSON(), {
        courseModel: this.courseModel.toJSON()
      });
      this.$el.html(_.template($('#review-tpl').html(), context));

      // TODO(david): Make this prettier and conform to our styles
      // TODO(david): Allow adding a prof
      this.$('.prof-select').select2({
      });

      if (this.userReviewModel.has('prof_id')) {
        this.$('.prof-select')
          .select2('val', this.userReviewModel.get('prof_id'));
        this.$('.add-review')
          .html('<i class="icon-edit"></i> Edit review');
      }

      this.$('.comments')
        .autosize()
        .height(70)  // Because autosize doesn't respect CSS class height
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
      // TODO(david): Should initially be in this state if user had review
      // TODO(david): Use spinner instead of static time icon
      var button = this.$('.save-review');
      button
        .removeClass('btn-primary btn-success')
        .addClass('btn-warning')
        .prop('disabled', true)
        .html('<i class="icon-time"></i> Saving...');

      this.saving = true;
      var self = this;

      this.userReviewModel.save({
        //id: this.userReviewModel.get('id'),
        //term_id: this.userReviewModel.get('term_id'),
        professor_id: this.$('.prof-select').select2('val'),
        course_id: this.courseModel.get('id'),
        course_review: _.extend({}, this.userReviewModel.get('course_review'), {
          comment: this.$('.course-comments').val()
        }),
        professor_review: _.extend({}, this.userReviewModel.get('professor_review'), {
          comment: this.$('.prof-comments').val()
        })
      }).done(function() {
        button
          .removeClass('btn-warning')
          .addClass('btn-success')
          .prop('disabled', true)
          .html('<i class="icon-ok"></i> Saved.');
      }).error(function() {
        button
          .removeClass('btn-warning')
          .addClass('btn-danger')
          .prop('disabled', false)
          .html('<i class="icon-exclamation-sign"></i> Error! :( Try again.');
      }).always(function() {
        self.saving = false;
      });
    },

    allowSave: function() {
      if (this.saving) {
        return;
      }

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
