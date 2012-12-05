define(
['rmc_backbone', 'ext/jquery', 'ext/jqueryui', 'ext/underscore',
'ext/underscore.string', 'ratings', 'ext/select2', 'ext/autosize', 'course',
'user', 'ext/bootstrap', 'prof', 'facebook', 'util', 'ext/toastr'],
function(RmcBackbone, $, _jqueryui, _, _s, ratings, _select2, _autosize,
    _course, _user, _bootstrap, _prof, _facebook, _util, _toastr) {

  // TODO(david): This should probably go in term.js (but circular dep) and also
  //     leaky abstraction from server.
  var SHORTLIST_TERM_ID = '9999_99';

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
      professor_review: null,
      course_review: null,
      has_reviewed: null
    },

    // Function needed since UserCourses in defined later in file.
    // TODO(david): Use strings for reference field to avoid this fn
    referenceFields: function() {
      return {
        'user': [ 'user_id', _user.UserCollection ],
        'course': [ 'course_id', _course.CourseCollection ],
        'professor': [ 'professor_id', _prof.ProfCollection ]
      };
    },

    url: function() {
      return '/api/user/course';
    },

    initialize: function(attrs) {
      // TODO(mack): fix potential bug here, since professor_review
      // and course_review are are objects that are potentially shared
      // among all UserCourse models
      this.set('professor_review', new UserComment(attrs ?
            attrs.professor_review : undefined));
      this.set('course_review', new UserComment(attrs ?
            attrs.course_review : undefined));

      // TODO(david): This feels a little weird...
      this.get('professor_review').set('ratings',
        new ratings.RatingChoiceCollection(
          this.get('professor_review').get('ratings')));
      this.get('course_review').set('ratings',
        new ratings.RatingChoiceCollection(
          this.get('course_review').get('ratings')));

      this.on('sync', _.bind(this.onSync, this));
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

    onSync: function(model, response, options) {
      this.gainPoints(response.points_gained);
    },

    gainPoints: function(numPoints) {
      this.get('user').gainPoints(numPoints);
    },

    getReviewJson: function(reviewType) {
      var review = this.get(reviewType);
      return _.extend({}, review, { 'ratings': review.get('ratings').toJSON() });
    },

    hasComments: function() {
      // TODO(david): Use date when we fix that on the server
      return this.get('professor_review').comment ||
          this.get('course_review').comment;
    },

    getProgramName: function() {
      return this.get('user').get('program_name');
    },

    getOverallRating: function() {
      return this.get('course_review').get('ratings').find(function(rating) {
        return rating.get('name') === 'interest';
      });
    },

    promptPostToFacebook: function(reviewType) {
      var name = '';
      var description = '';
      var caption = 'on Flow';

      var courseCode = this.get('course').get('code');
      // TODO(Sandy): Turn these into enums or something?
      if (reviewType === 'COURSE') {
        name = 'I reviewed ' + courseCode;
        description = this.get('course_review').get('comment');
      } else if (reviewType === 'PROFESSOR') {
        name = 'I commented on my ' + courseCode + ' professor ' +
            this.get('professor').get('name');
        description = this.get('professor_review').get('comment');
      }
      description = _util.truncatePreviewString(description, 50);

      var callback = _.bind(function(response) {
        // response.post_id is returned on success
        // response === null on "Cancel"
        if (response && response.post_id) {
          // TODO(sandy): Award points!
          // Give UI feedback with toastr
          var msg;
          if (reviewType === 'COURSE') {
            msg = _s.sprintf('Shared review for %s on Facebook!',
                this.get('course').get('code'));
          } else if (reviewType === 'PROFESSOR') {
            msg = _s.sprintf('Shared comment on %s for %s on Facebook!',
                this.get('professor').get('name'),
                this.get('course').get('code'));
          }
          toastr.success(msg);

          this.onShareSuccess(reviewType);

          // Facebook engagement completed
          mixpanel.track('Facebook share review completed', {
            ReviewType: reviewType
          });
          mixpanel.people.increment({'Facebook share review completed': 1});
        }
      }, this);

      // TODO(Sandy): Implement proper review showing, if people actually share
      var link = 'http://uwflow.com/course/' + this.get('course').get('id');
      _facebook.showFeedDialog(link, name, caption, description, callback);
      // Facebook engagement intent
      mixpanel.track('Facebook share review intent', {
        ReviewType: reviewType
      });
      mixpanel.people.increment({'Facebook share review intent': 1});
    },

    onShareSuccess: function(reviewType) {
      if (reviewType == 'COURSE') {
        reviewType = 'course';
      } else if (reviewType == 'PROFESSOR') {
        reviewType = 'professor';
      }

      var data = {
        user_course_id: this.id,
        review_type: reviewType
      };

      $.ajax('/api/user/course/share', {
        type: 'POST',
        dataType: 'json',
        data: data,
        success: _.bind(this.onShareSuccessResponse, this)
      });
    },

    onShareSuccessResponse: function(response) {
      this.gainPoints(response.points_gained);
    },

    hasTaken: function() {
      return this.get('term_id') && this.get('term_id') !== SHORTLIST_TERM_ID;
    },

    // TODO(david): Properly determine if user ever has rated/commented by using
    //     date
    // TODO(david): Factor out star into its own Backbone view+model
    hasRatedCourse: function() {
      // TODO(david): Law of demeter-ize this and rest of similar functions
      return this.get('course_review').get('ratings').hasRated();
    },

    hasRatedProf: function() {
      return this.get('professor_review').get('ratings').hasRated();
    },

    hasReviewedCourse: function() {
      return this.get('course_review').get('comment');
    },

    hasReviewedProf: function() {
      return this.get('professor_review').get('comment');
    }
  });

  var UserCourses = RmcBackbone.Collection.extend({
    model: UserCourse
  });
  UserCourses.registerCache('user_course');

  var UserCourseView = RmcBackbone.View.extend({
    initialize: function(options) {
      this.userCourse = options.userCourse;
      this.courseModel = options.courseModel;

      var courseReview = this.userCourse.get('course_review');
      var profReview = this.userCourse.get('professor_review');

      this.courseCommentView = new UserCommentView({
        review: courseReview,
        userCourse: this.userCourse,
        className: 'user-comment course-comment',
        placeholder: 'Post any tips or comments and earn 50 points!',
        reviewType: 'COURSE'
      });
      this.profCommentView = new UserCommentView({
        review: profReview,
        userCourse: this.userCourse,
        className: 'user-comment prof-comment',
        // TODO(mack): get number of points from backend
        placeholder: 'Comment about the professor and earn 50 points!',
        reviewType: 'PROFESSOR'
      });

      courseReview.on('change:comment', _.bind(this.saveComments, this,
            this.courseCommentView, 'COURSE'));
      profReview.on('change:comment', _.bind(this.saveComments, this,
            this.profCommentView, 'PROFESSOR'));

      var courseRatings = this.userCourse.get('course_review').get('ratings');
      var profRatings = this.userCourse.get('professor_review').get('ratings');

      this.courseRatingsView = new ratings.RatingChoiceCollectionView({
        collection: courseRatings
      });
      this.profRatingsView = new ratings.RatingChoiceCollectionView({
        collection: profRatings
      });

      // TODO(david): Should be a change on model triggers save
      courseRatings.on('change', _.bind(this.saveRatings, this, 'COURSE'));
      profRatings.on('change', _.bind(this.saveRatings, this, 'PROFESSOR'));

      this.profNames = this.courseModel.get('professors').pluck('name');
      this.profIds = this.courseModel.get('professors').pluck('id');
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
        program_name: this.userCourse.getProgramName(),
        user_name: this.userCourse.get('user').get('name')
      });
      this.$el.html(_.template($('#add-review-tpl').html(), context));

      this.$('.course-comment-placeholder').replaceWith(
          this.courseCommentView.render().el);
      this.$('.prof-comment-placeholder').replaceWith(
          this.profCommentView.render().el);

      // TODO(david): Make this prettier and conform to our styles
      // TODO(david): Show "Add..." option
      var $profSelect = this.$('.prof-select');
      $profSelect.select2({
        createSearchChoice: function(term) {
          // Only create search items if no prefix match
          if (self.matchesProf(term)) return null;
          return {
            id: term,
            text: term
          };
        },
        initSelection : function (element, callback) {
          // Select2 is weird
        },
        allowClear: true,
        data: this.courseModel.get('professors')
          .chain()
          .sortBy(function(prof) {
            return prof.get('name');
          })
          .map(function(prof) {
            return { id: prof.id, text: prof.get('name') };
          })
          .value()
      });

      if (this.userCourse.has('professor_id')) {
        var profId = this.userCourse.get('professor_id');
        // TODO(mack): should be looking up prof from prof cache once all pages
        // are refactored to work with prof cache
        var prof = this.courseModel.getProf(profId);
        if (prof) {
          this.$('.prof-select')
            .select2('data', { id: profId, text: prof.get('name') });
        }
        this.$('.prof-review').show();
      }

      this.$('.course-ratings-placeholder').replaceWith(
          this.courseRatingsView.render().el);
      this.$('.prof-ratings-placeholder').replaceWith(
          this.profRatingsView.render().el);

      this.$('.dropdown-toggle').dropdown();

      return this;
    },

    events: {
      'change .prof-select': 'onProfSelect'
    },

    logToGA: function(event, label) {
      // TODO(Sandy): Include more info like course_id
      // NOTE: The 4th param "value" can ONLY be an integer
      _gaq.push([
        '_trackEvent',
        'USER_ENGAGEMENT',
        event,
        label
      ]);
    },

    onProfSelect: function() {
      var profData = this.$('.prof-select').select2('data');
      if (profData) {
        this.$('.prof-review').slideDown(300, 'easeOutCubic');
      } else {
        this.$('.prof-review').slideUp(300, 'easeOutCubic');
      }
      this.logToGA('PROFESSOR', 'SELECT');
      this.save();

      mixpanel.track('Reviewing: Professor selected', {
        course_id: this.userCourse.get('course_id')
      });
      mixpanel.people.increment({'Professor selected': 1});
    },

    saveComments: function(view, reviewType) {
      this.logToGA(reviewType, 'REVIEW');
      this.save()
        .done(_.bind(view.saveSuccess, view))
        .error(_.bind(view.saveError, view));

      mixpanel.track('Reviewing: Save comments', {
        review_type: reviewType,
        course_id: this.userCourse.get('course_id')
      });
      mixpanel.people.increment({'Reviewed': 1});
    },

    saveRatings: function(ratingType) {
      this.logToGA(ratingType, 'RATING');
      this.save();

      mixpanel.track('Reviewing: Save Ratings', {
        rating_type: ratingType,
        course_id: this.userCourse.get('course_id')
      });
      mixpanel.people.increment({'Rated': 1});
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
    }

  });

  var UserComment = RmcBackbone.Model.extend({
    defaults: {
      comment: '',
      comment_date: null,
      privacy: 'friends'
    }
  });

  var UserCommentView = RmcBackbone.View.extend({
    className: 'user-comment',

    initialize: function(options) {
      this.review = options.review;
      this.userCourse = options.userCourse;
      this.placeholder = options.placeholder;
      this.reviewType = options.reviewType;
      this.template = _.template($('#user-comment-tpl').html());
    },

    render: function() {
      this.$el.html(this.template(_.extend(this.review.toJSON(), {
        placeholder: this.placeholder,
        user_name: this.userCourse.get('user').get('name')
      })));

      var $comments = this.$('.comments')
        .autosize({ bottomFeed: 3 })
        .css('resize', 'none');

      // Get autosize to adjust
      _.defer(function() { $comments.trigger('input'); });

      if (this.review.get('comment')) {
        this.showShare();
        this.onFocus();
      }

      this.setPrivacy(this.review.get('privacy'));

      return this;
    },

    events: {
      'focus .comments': 'onFocus',
      'click .save-review': 'onSave',
      'click .share-review': 'onShare',
      'keyup .comments': 'allowSave',
      'click .privacy-tip .dropdown-menu li': 'onPrivacySelect'
    },

    onFocus: function() {
      this.$('.submit-bar').fadeIn(300);
      this.$('.comments').trigger('input');
    },

    onSave: function() {
      this.review.set('comment', this.$('.comments').val());

      this.$('.save-review')
        .removeClass('btn-primary btn-success')
        .addClass('btn-warning')
        .prop('disabled', true)
        .html('<i class="icon-time"></i> Saving...');

      this.saving = true;
    },

    onShare: function() {
      this.userCourse.promptPostToFacebook(this.reviewType);
    },

    allowSave: function() {
      if (this.saving || !this.review.get('comment')) return;

      this.$('.share-review')
        .removeClass('share-review')
        .addClass('save-review');

      this.$('.save-review')
        .removeClass('btn-info btn-warning btn-danger')
        .addClass('btn-primary')
        .prop('disabled', false)
        .html('<i class="icon-save"></i> Update!')
        // destroy the share to get points tooltip
        .tooltip('destroy');
    },

    showShare: function() {
      var tooltipText;
      if (this.reviewType === 'COURSE') {
        tooltipText = 'Share this course review to earn 50 points!';
      } else if (this.reviewType === 'PROFESSOR') {
        tooltipText = 'Share this professor review to earn 50 points!';
      }

      this.saving = false;
      this.$('.save-review')
        .removeClass('btn-warning btn-danger btn-primary save-review')
        .addClass('btn-info share-review')
        .prop('disabled', false)
        .html('<i class="icon-share"></i> Share')
        // TODO(mack): get number of points for action from backend
        // TODO(mack): do not show this if they have already shared
        // the course
        .tooltip({ title: tooltipText });
    },

    saveSuccess: function() {
      this.showShare();
      // Give UI feedback with toastr
      var msg = '';
      if (this.reviewType === 'COURSE') {
        msg = _s.sprintf('Comments on %s saved!',
            this.userCourse.get('course').get('code'));
      } else if (this.reviewType === 'PROFESSOR') {
        msg = _s.sprintf('Comments on %s for %s saved!',
            this.userCourse.get('professor').get('name'),
            this.userCourse.get('course').get('code'));
      }
      toastr.success(msg);
    },

    saveError: function() {
      this.saving = false;
      this.$('.save-review')
        .removeClass('btn-warning')
        .addClass('btn-danger')
        .prop('disabled', false)
        .html('<i class="icon-exclamation-sign"></i> ' +
            'Error :( Try again');
    },

    onPrivacySelect: function(evt) {
      $target = $(evt.currentTarget);
      var setting = $target.data('value');
      this.setPrivacy(setting);
      this.review.set('privacy', setting);
    },

    setPrivacy: function(setting) {
      var html = this.$(
          '.privacy-tip .dropdown-menu [data-value="' + setting + '"] a')
        .html();
      this.$('.current-privacy').html(html);

      var tooltip = {
        everyone: 'Your comments will be public',
        friends: 'Others see "A ' + this.userCourse.getProgramName() +
            ' student"',
        me: 'Post anonymously; no one will know who wrote this.'
      }[setting];

      this.$('.privacy-tip-more-info')
        .tooltip('destroy')  // Bootstrap is stupid
        .tooltip({ title: tooltip });
    }
  });


  return {
    UserCourse: UserCourse,
    UserCourses: UserCourses,
    UserCourseView: UserCourseView
  };
});
