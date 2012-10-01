define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'ext/select2', 'ext/autosize', 'course', 'user', 'ext/bootstrap'],
function(RmcBackbone, $, _, _s, ratings, _select2, _autosize, _course, _user,
  _bootstrap) {

  // TODO(david): Refactor to use sub-models for reviews
  // TODO(david): Refactor this model to match our mongo UserCourse model
  var UserCourse = RmcBackbone.Model.extend({
    // TODO(mack): use undefined rather than null
    defaults: {
      id: null,
      term_id: null,
      term_name: null,
      course_id: null,
      professor_id: null,
      professor_review: {
        ratings: [],
        comment: '',
        comment_date: null
      },
      course_review: {
        ratings: [],
        comment: '',
        comment_date: null
      },
      friend_user_course_ids: []
    },

    // Function needed since UserCourses in defined later in file.
    referenceFields: function() {
      return {
        'user': [ 'user_id', _user.UserCollection ],
        'course': [ 'course_id', _course.CourseCollection ],
        'friend_user_courses': [ 'friend_user_course_ids', UserCourses ]
      };
    },

    url: function() {
      return '/api/user/course';
    },

    initialize: function(attrs) {
      this.get('professor_review').ratings = new ratings.RatingChoiceCollection(
          attrs.professor_review.ratings);
      this.get('course_review').ratings = new ratings.RatingChoiceCollection(
          attrs.course_review.ratings);
    },

    parse: function(attrs) {
      this.get('professor_review').comment_date = attrs[
        'professor_review.comment_date'];
      this.get('course_review').comment_date = attrs[
        'course_review.comment_date'];
      // We return nothing because we have a nested collection which can't be
      // just replaced over because it has event handlers.
      return {};
    },

    getReviewJson: function(reviewType) {
      var review = this.get(reviewType);
      return _.extend({}, review, { 'ratings': review.ratings.toJSON() });
    },

    validate: function(attrs) {
      // TODO(david): Make this make more sense
      if (attrs.professor_review.comments && !attrs.professor_id &&
          !this.get('professor_id')) {
        return "Which professor did you take the course with?";
      }
    },

    hasComments: function() {
      // TODO(david): Use date when we fix that on the server
      return this.get('professor_review').comment ||
          this.get('course_review').comment;
    }
  });

  var UserCourses = RmcBackbone.Collection.extend({
    model: UserCourse
  });
  UserCourses.registerCache('user_course');

  var UserCourseView = RmcBackbone.View.extend({
    events: {
      'change .prof-select': 'showReview',
      'click .add-review': 'showReview',
      'click .save-review': 'saveComments',
      'keyup .comments': 'allowSave'
    },

    initialize: function(options) {
      this.userCourse = options.userCourse;
      this.courseModel = options.courseModel;

      var courseRatings = this.userCourse.get('course_review').ratings;
      var profRatings = this.userCourse.get('professor_review').ratings;

      this.courseRatingsView = new ratings.RatingChoiceCollectionView({
        collection: courseRatings
      });
      this.profRatingsView = new ratings.RatingChoiceCollectionView({
        collection: profRatings
      });

      courseRatings.on('change', _.bind(this.save, this, {}, {}));
      profRatings.on('change', _.bind(this.save, this, {}, {}));

      this.profNames = _.pluck(this.courseModel.get('professors'), 'name');
      this.profIds = _.pluck(this.courseModel.get('professors'), 'id');
      // TODO(david): Find a way to get select2 to not create search choice
      //     until a non-match for us (instead of manually doing this).
      this.matchesProf = _.bind(function(term) {
        return _.find(this.profNames, _.bind(
              $.fn.select2.defaults.matcher, null, term));
      }, this);
    },

    render: function() {
      var self = this;
      var context = _.extend(this.userCourse.toJSON(), {
        courseModel: this.courseModel.toJSON(),
        program_name: this.userCourse.get('user').get('program_name')
      });
      this.$el.html(_.template($('#add-review-tpl').html(), context));

      // TODO(david): Make this prettier and conform to our styles
      // TODO(david): Show "Add..." option
      var $profSelect = this.$('.prof-select');
      $profSelect.select2({
        createSearchChoice: function(term) {
          // Only create search items if no prefix match
          if (self.matchesProf(term)) return null;
          return {
            id: term,
            text: 'new course prof ' + term
          };
        },
        initSelection : function (element, callback) {
          // TODO(david): Figure out if this is needed
          //var data = [];
          //$(element.val().split(",")).each(function() {
            //data.push({ id: this, text: this });
          //});
          //callback(data);
        },
        data: this.courseModel.get('professors').map(function(prof) {
          return { id: prof.id, text: prof.name };
        })
      });

      if (this.userCourse.has('professor_id')) {
        var profId = this.userCourse.get('professor_id');
        var prof = this.courseModel.getProf(profId);
        if (prof) {
          this.$('.prof-select')
            .select2('data', { id: profId, text: prof.name });
        }
        // TODO(david): Set button to say edit if there's any userCourse content
        this.$('.add-review')
          .html('<i class="icon-edit"></i> Edit review');
      }

      if (this.userCourse.hasComments()) {
        this.saveButtonSuccess();
      }

      this.$('.comments')
        .autosize()
        .height(60)  // Because autosize doesn't respect CSS class height
        .css('resize', 'none');

      this.$('.course-ratings-placeholder').replaceWith(
          this.courseRatingsView.render().el);
      this.$('.prof-ratings-placeholder').replaceWith(
          this.profRatingsView.render().el);

      this.$('.privacy-tip-more-info').tooltip();

      return this;
    },

    showReview: function() {
      this.$('.review-details').slideDown();
      this.$('.add-review').fadeOut('fast');
    },

    saveComments: function() {
      // TODO(david): Should initially be in this state if user had review
      // TODO(david): Use spinner instead of static time icon
      var button = this.$('.save-review');
      button
        .removeClass('btn-primary btn-success')
        .addClass('btn-warning')
        .prop('disabled', true)
        .html('<i class="icon-time"></i> Saving...');

      var profReview = _.extend({}, this.userCourse.get('professor_review'), {
        comment: this.$('.prof-comments').val()
      });
      var courseReview = _.extend({}, this.userCourse.get('course_review'), {
        comment: this.$('.course-comments').val()
      });

      this.saving = true;
      var self = this;

      var saveXhr = this.save({
        'professor_review': profReview,
        'course_review': courseReview
      }, {
        error: function(model, error) {
          // Bring down the choose professor box if no prof chosen
          // TODO(david): Actually throw an error subclass and test which error
          if (_.isString(error) && error.indexOf('hich professor')) {
            self.$('.prof-select-row')
              .hide()
              .appendTo(self.$('.user-course'))
              .css('margin-top', '10px')
              .addClass('text-error')
              .fadeIn('slow');
          }
        }
      });

      var onError = function() {
        button
          .removeClass('btn-warning')
          .addClass('btn-danger')
          .prop('disabled', false)
          .html('<i class="icon-exclamation-sign"></i> ' +
              'Oh noes, that didn\'t work :( Try again');
      };

      if (saveXhr) {
        saveXhr.done(function() {
          self.saveButtonSuccess();
        }).error(onError).always(function() {
          self.saving = false;
        });
      } else {
        onError();
        self.saving = false;
      }
    },

    save: function(attrs, options) {
      var profData = this.$('.prof-select').select2('data');
      var profId = profData && profData.id;
      var newProfAdded = _.contains(this.profIds, profId) ? false : profId;

      return this.userCourse.save(_.extend({
        professor_id: profId,
        new_prof_added: newProfAdded,
        course_id: this.courseModel.get('id')
      }, attrs), options);
    },

    saveButtonSuccess: function() {
      this.$('.save-review')
        .removeClass('btn-warning btn-danger btn-primary')
        .addClass('btn-success')
        .prop('disabled', true)
        .html('<i class="icon-ok"></i> Comments saved.');
    },

    allowSave: function() {
      if (this.saving) {
        return;
      }

      this.$('.save-review')
        .removeClass('btn-success btn-warning btn-danger')
        .addClass('btn-primary')
        .prop('disabled', false)
        .html('<i class="icon-save"></i> Update comments!');
    }
  });


  return {
    UserCourse: UserCourse,
    UserCourses: UserCourses,
    UserCourseView: UserCourseView
  };
});
