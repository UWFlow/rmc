define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'ext/bootstrap', 'util', 'jquery.slide', 'prof', 'ext/toastr',
'section', 'work_queue', 'sign_in'],
function(RmcBackbone, $, _, _s, ratings, __, util, jqSlide, _prof, toastr,
    _section, _work_queue, sign_in) {

  var CourseModel = RmcBackbone.Model.extend({
    defaults: {
      id: 'SCI 238',
      name: 'Introduction to Astronomy omg omg omg',
      description: 'This couse will introduce you to the wonderful world' +
        ' of astronomy. Learn about the Milky Way, the Big Bang, and' +
        ' everything in between. Become enthralled in the wonderful' +
        ' world of astronomy.',
      ratings: [{
        name: 'usefulness',
        count: 0,
        total: 0
      }, {
        name: 'easiness',
        count: 7,
        total: 2
      }],
      user_course_id: undefined,
      profile_user_course_id: undefined,
      friend_user_course_ids: [],
      professor_ids: [],
      prereqs: undefined
    },

    referenceFields: function() {
      // TODO(mack): remove require() call
      var _user_course = require('user_course');
      return {
        'user_course': [
          'user_course_id', _user_course.UserCourses
        ],
        'profile_user_course': [
          'profile_user_course_id', _user_course.UserCourses
        ],
        'friend_user_courses': [
          'friend_user_course_ids', _user_course.UserCourses
        ],
        'professors': [
          'professor_ids', _prof.ProfCollection
        ]
      };
    },

    initialize: function(attributes) {
      // TODO(david): Be consistent in the way we return ratings from the server
      if (attributes.ratings) {
        var isOverall = function(rating) { return rating.name === 'interest'; };
        var filteredRatings = _.reject(attributes.ratings, isOverall);
        var overallRating = _.find(attributes.ratings, isOverall);

        this.set('ratings', new ratings.RatingCollection(filteredRatings));
        this.set('overall', new ratings.RatingModel(overallRating));
      }

      if (attributes.sections) {
        this.set('sections',
            new _section.SectionCollection(attributes.sections));
      }
    },

    getProf: function(id) {
      return this.get('professors').find(function(prof) {
        return prof.id === id;
      });
    },

    getOverallRating: function() {
      return this.get('overall');
    },

    /**
     * Returns the html representation of pre-req str with proper linking
     * of courses. Mark courses that the current user has taken with a
     * special class
     *
     * TODO(mack): Show course name on hover, and for courses you've taken
     * show what term you took it.
     */
    getReqsHtml: function(reqsStr) {

      var takenCourseIds = {};
      if (pageData.currentUserId) {
        // TODO(mack): remove require() call
        var _user = require('user');
        var userId = pageData.currentUserId.$oid;
        var user = _user.UserCollection.getFromCache(userId);
        _.each(user.get('course_ids'), function(courseId) {
          takenCourseIds[courseId] = true;
        });
      }

      // TODO(mack): highlight courses you've taken
      var splits = reqsStr.split(/(\W+)/);
      var newSplits = [];
      _.each(splits, function(split) {
        var matchesCourseId = !!split.match(/^[A-Z]{2,}\d{3}[A-Z]?$/);
        var newSplit = split;
        if (matchesCourseId) {
          var splitLower = split.toLowerCase();

          // TODO(mack): use html elements rather than string concatentation
          if (_.has(takenCourseIds, splitLower)) {
            // If you've taken the course, add the css class 'taken'
            newSplit = _s.sprintf(
              '<a class="req taken" href="/course/%s">%s</a>',
              split.toLowerCase(), split);
          } else {
            newSplit = _s.sprintf(
              '<a class="req" href="/course/%s">%s</a>', split.toLowerCase(),
              split);
          }
        }
        newSplits.push(newSplit);
      });

      return newSplits.join('');
    },

    /**
     * Can the user add or remove the course to/from her profile?
     * @return {string|undefined} A string "add" or "remove" if interactable.
     */
    getInteractMode: function() {
      var userCourse = this.get('user_course');
      var mode = userCourse && userCourse.get('term_id') ? 'remove' : 'add';
      if (window.pageData.ownProfile === false && mode === 'remove') {
        return null;
      } else {
        return mode;
      }
    }
  });

  /**
   * A base interactable course view supporting add/remove courses.
   */
  var BaseCourseView = RmcBackbone.View.extend({

    initialize: function(attributes) {
      this.courseModel = attributes.courseModel;
      this.userCourse = attributes.userCourse;
    },

    onCourseAdd: function(callback) {
      var self = this;

      var onSuccess = function(resp) {
        //TODO(mack): consider alternative placement of toast so that it
        // doesn't potentially cover up the main nav
        toastr.success(
          _s.sprintf('%s was added to your shortlist!',
              self.courseModel.get('name'))
        );

        mixpanel.track('Add to shortlist', {
          course_id: self.courseModel.id
        });
        mixpanel.people.increment({'Add to shortlist': 1});

        // TODO(mack): remove require()
        var _user_course = require('user_course');
        // Add the new user course to the collection cache
        _user_course.UserCourses.addToCache(resp.user_course);
        self.userCourse = _user_course.UserCourses.getFromCache(
          resp.user_course.id);
        self.courseModel.set('user_course_id', self.userCourse.id);

        self.$('.add-course-btn').tooltip('destroy');

        if (self.courseAdded) {
          self.courseAdded();
        }
      };

      var _user = require('user');
      if (!_user.getCurrentUser()) {
        sign_in.renderLoginModal();
      } else {
        $.ajax('/api/v1/user/shortlist/' + this.courseModel.id, { type: 'PUT' })
          .done(onSuccess);
      }

      return false;
    },

    onCourseRemove: function(evt) {
      // Remove existing confirmation dialogs
      $('#confirm-remove-modal').remove();

      $('body').append(
        _.template($('#course-confirm-remove-dialog-tpl').html(), {
          course_code: this.courseModel.get('code')
        }));
      $('#confirm-remove-modal-button-yes').click(
          _.bind(this.removeCourse, this));

      $('#confirm-remove-modal').modal('show');

      mixpanel.track('Removed transcript course intent', {
        course_id: this.courseModel.id.$oid
      });
      mixpanel.people.increment({'Removed transcript course intent': 1});

      return false;
    },

    removeCourse: function() {
      $('#confirm-remove-modal').modal('hide');
      var onSuccess = _.bind(function(resp) {
        toastr.info(
          _s.sprintf('%s was removed!', this.courseModel.get('name'))
        );

        mixpanel.track('Removed transcript course', {
          course_id: this.courseModel.id.$oid
        });
        mixpanel.people.increment({'Removed transcript course': 1});

        // TODO(mack): remove require()
        var _user_course = require('user_course');
        // Remove the user course from the collection cache
        _user_course.UserCourses.removeFromCache(this.userCourse);
        this.courseModel.set('user_course_id', undefined);
        this.userCourse = undefined;

        this.$('.remove-course-btn').tooltip('destroy');
        if (pageData.ownProfile) {
          // We should only be removing the course card if the user is on their
          // own profile
          var onHide = _.bind(function() {
            // TODO(mack): properly destory subviews
            this.close();
          }, this);

          this.$el.slideUp(200, onHide);
        } else {
          this.render();
        }

      }, this);

      $.post(
        '/api/user/remove_course',
        {
          course_id: this.userCourse.get('course_id'),
          term_id: this.userCourse.get('term_id')
        },
        onSuccess
      );
    }

  });

  var CourseView = BaseCourseView.extend({
    MAX_REVIEW_LEVEL: 4,

    className: 'course',

    initialize: function(attributes) {
      this._super('initialize', [attributes]);

      this.courseModel = attributes.courseModel;
      this.userCourse = this.courseModel.get('user_course');
      // TODO(mack): Might not always be appropriate to just fetch
      // profileUserCourse like this since it's only gettable from
      // profile page
      this.profileUserCourse = this.courseModel.get('profile_user_course');
      this.otherProfile = pageData.ownProfile === false;

      if (this.userCourse && this.profileUserCourse &&
          this.profileUserCourse.hasTaken()) {
        var _user_course = require('user_course');
        this.reviewStarsView = new _user_course.ReviewStarsView({
          userCourse: this.userCourse
        });
      }

      this.canShowAddReview =
        'canShowAddReview' in attributes ? attributes.canShowAddReview : true;
      this.template = _.template($('#course-tpl').html());
    },

    updateAddCourseTooltip: function() {
      var title;
      if (pageData.currentUserId) {
        title = 'Add to my shortlist';
      } else {
        title = 'Log in to add courses to your profile';
      }
      this.$('.add-course-btn')
        .tooltip('destroy')
        .tooltip({
          title: title,
          placement: 'right',
          animation: false
        });
    },

    updateRemoveCourseTooltip: function() {
      this.$('.remove-course-btn')
        .tooltip('destroy')
        .tooltip({
          title: 'Remove from profile',
          placement: 'right',
          animation: false
        });
    },

    render: function() {
      var domId = 'course-view-' + this.courseModel.get('user_course_id');
      this.$el.attr('id', domId).html(this.template({
        course: this.courseModel.toJSON(),
        user_course: this.userCourse,
        profile_user_course: this.profileUserCourse,
        other_profile: this.otherProfile,
        mode: this.courseModel.getInteractMode()
      }));

      this.$('[title]').tooltip();

      var overallRating = this.courseModel.getOverallRating();
      this.ratingBoxView = new ratings.RatingBoxView({ model: overallRating });

      _work_queue.add(function() {
        var friendUserCourses = this.courseModel.get('friend_user_courses');
        if (friendUserCourses) {
          this.sampleFriendsView = new SampleFriendsView({
            friendUserCourses: friendUserCourses
          });

          this.$('.sample-friends-placeholder').replaceWith(
            this.sampleFriendsView.render().$el);
        }
      }, this);

      this.updateAddCourseTooltip();
      this.updateRemoveCourseTooltip();

      if (this.canShowAddReview &&
          this.userCourse &&
          this.userCourse.hasTaken()) {
        this.votingView = new ratings.RatingChoiceView({
          model: this.userCourse.getOverallRating(),
          voting: true,
          className: 'voting'
        });
        this.$('.voting-placeholder').replaceWith(this.votingView.render().el);
      }

      this.$('.rating-box-placeholder').replaceWith(
          this.ratingBoxView.render().$el);

      if (this.courseInnerView) {
        delete this.courseInnerView;
        if (this.$el.hasClass('expanded')) {
          this.expandCourse();
        }
      }

      if (!this.resizeBounded) {
        $(window).on('resize', _.bind(this.onResize, this));
        this.resizeBounded = true;
      }
      _.defer(_.bind(this.onResize, this));

      if (this.reviewStarsView) {
        this.$('.review-stars-placeholder').replaceWith(
            this.reviewStarsView.render().el);
      }

      return this;
    },

    onResize: function() {
      // TODO(david): Try to do this in CSS
      var codeWidth = this.$('.course-code').width();
      var barWidth = this.$('.visible-section').width();
      this.$('.course-name').width(Math.min(300, barWidth - 310 - codeWidth));
    },

    events: {
      'click .add-course-btn': 'onCourseAdd',
      'click .remove-course-btn': 'onCourseRemove',
      // TODO(david): Figure out a nicer interaction without requiring click
      'click .visible-section': 'toggleCourse',
      'focus .new-review-input': 'expandNewReview',
      'expand': 'expandCourse'
    },

    courseAdded: function() {
      this.updateRemoveCourseTooltip();
      this.render();
    },

    toggleCourse: function(evt) {
      if (this.$('.course-inner').is(':visible')) {
        // Don't collapse if a link is being clicked
        if (!$(evt.target).is('a')) {
          this.collapseCourse(evt);
        }
      } else {
        this.expandCourse(evt);
      }
    },

    expandCourse: function(evt) {
      if (!this.courseInnerView) {
        this.courseInnerView = new CourseInnerView({
          courseModel: this.courseModel,
          userCourse: this.userCourse,
          canShowAddReview: this.canShowAddReview,
          courseView: this
        });

        // TODO(david): Neaten this jQuery
        var $inner = this.courseInnerView.render(/* moreDetails */ true).$el;
        $inner.addClass('hide-initial');
        this.$('.course-inner-placeholder').replaceWith($inner);
      }

      this.$el.addClass('expanded');
      this.courseInnerView.$el.show();
      this.courseInnerView.animateBars(0);
    },

    collapseCourse: function(evt) {
      this.$('.course-inner').hide();
      this.$el.removeClass('expanded');
    },

    expandNewReview: function(evt) {
      this.$('.new-review').addClass('new-review-expanded');
    }
  });

  // TODO(david): Refactor things to use implicit "model" on views
  var CourseInnerView = BaseCourseView.extend({
    className: 'course-inner',

    initialize: function(attributes) {
      this.courseModel = attributes.courseModel;
      this.userCourse = attributes.userCourse;
      this.canShowAddReview =
        'canShowAddReview' in attributes ? attributes.canShowAddReview : true;
      this.canReview =
          this.userCourse &&
          this.userCourse.hasTaken() &&
          this.canShowAddReview;
      this.courseView = attributes.courseView;  // optional
      this.shouldLinkifySectionProfs = (
          attributes.shouldLinkifySectionProfs || false);

      this.ratingsView = new ratings.RatingsView({
        ratings: this.courseModel.get('ratings'),
        userCourse: this.userCourse,
        subject: 'course'
      });

      if (this.canReview) {
        // TODO(david): Get user review data, and don't show or show atered if
        // no user or user didn't take course.
        // TODO(mack): remove circular dependency
        var _user_course = require('user_course');
        this.userCourseView = new _user_course.UserCourseView({
          userCourse: this.userCourse,
          courseModel: this.courseModel
        });
      }

      if (this.courseModel.has('sections')) {
        this.sectionCollectionView = new _section.SectionCollectionView({
          collection: this.courseModel.get('sections'),
          shouldLinkifyProfs: this.shouldLinkifySectionProfs
        });
      }

      this.template = _.template($('#course-inner-tpl').html());
    },

    render: function(moreDetails) {
      this.$el.html(this.template({
        more_details: moreDetails,
        course: this.courseModel,
        user_course: this.userCourse,
        user: this.userCourse && this.userCourse.get('user'),
        can_review: this.canReview,
        mode: this.courseModel.getInteractMode()
      }));

      if (this.userCourseView) {
        this.$('.review-placeholder').replaceWith(
          this.userCourseView.render().el);
      }

      this.$('.ratings-placeholder').replaceWith(this.ratingsView.render().el);

      if (this.sectionCollectionView) {
        this.$('.section-collection-placeholder').replaceWith(
          this.sectionCollectionView.render().el);
      }

      return this;
    },

    events: function() {
      if (this.courseView) {
        return {};
      } else {
        return {
          'click .add-course-btn': 'onCourseAdd',
          'click .remove-course-btn': 'onCourseRemove'
        };
      }
    },

    animateBars: function(pause) {
      pause = pause === undefined ? 0 : pause;
      this.ratingsView.removeBars();

      window.setTimeout(_.bind(function() {
        this.ratingsView.render();
      }, this), pause);

      return this;
    },

    courseAdded: function() {
      this.render();
    }
  });

  var SampleFriendsView = RmcBackbone.View.extend({
    MAX_SAMPLE_FRIENDS: 3,

    className: 'sample-friends',

    initialize: function(attributes) {
      this.friendUserCourses = attributes.friendUserCourses;
      this.friendViews = [];
    },

    render: function() {
      this.$el.html(
        _.template($('#sample-friends-tpl').html(), {
          num_friends: this.friendUserCourses.length,
          max_sample_friends: this.MAX_SAMPLE_FRIENDS
        })
      );

      // TODO(mack): circular dependency here, maybe should have single
      // module that has all models like the backend
      var _user = require('user');
      var sampleFriendCollection = new _user.UserCollection(
        this.friendUserCourses.first(this.MAX_SAMPLE_FRIENDS)
      );
      var friendCollectionView = new FriendCollectionView({
        friendUserCourses: sampleFriendCollection
      });
      this.$('.friend-collection-placeholder').replaceWith(
        friendCollectionView.render().$el);

      var $target = this.$('.remaining-friends');

      // TODO(mack): investigate if offset attribute works for popover, need to
      // move popover slightly higher
      $target.popover({
        html: true,
        content: _.bind(this.getFriendsPopoverContent, this),
        trigger: 'hover',
        placement: 'in bottom'
      });
      // Prevent clicking in the hovercard from expanding/collapsing the course
      // view
      $target.on('click', '.popover', function(evt) {
        return false;
      });

      return this;
    },

    getFriendsPopoverContent: function() {
      if (!this.friendsHovercardView) {
        // TODO(mack): remove require()
        var _user_course = require('user_course');
        var remainingUserCourses = new _user_course.UserCourses(
          this.friendUserCourses.rest(this.MAX_SAMPLE_FRIENDS)
        );
        this.friendsHovercardView = new FriendCollectionView({
          friendUserCourses: remainingUserCourses
        });
      }
      // TODO(mack): custom width based on number of friends in hovercard
      return this.friendsHovercardView.render().$el;
    }

  });

  // Rename since it no longer holds FriendCollectionView
  var FriendCollectionView = RmcBackbone.View.extend({
    tagName: 'ul',
    className: 'friend-collection clearfix',

    initialize: function(attributes) {
      this.friendUserCourses = attributes.friendUserCourses;
      this.friendViews = [];
    },

    render: function() {
      this.$el.html(
        _.template($('#course-friends-hovercard-tpl').html(), {})
      );
      this.friendUserCourses.each(function(userCourse) {
        this.addFriend(userCourse);
      }, this);

      return this;
    },

    addFriend: function(userCourse) {
      var friendView = new CourseFriendView({
        userCourse: userCourse,
        tagName: 'li'
      });
      this.$el.append(friendView.render().el);
      this.friendViews.push(friendView);
    }

  });

  var CourseFriendView = RmcBackbone.View.extend({
    className: 'friend-pic',

    initialize: function(attributes) {
      this.userCourse = attributes.userCourse;
    },

    render: function() {
      this.$el.html(
        _.template($('#course-friend-tpl').html(), {
          friend: this.userCourse.get('user').toJSON()
        }
      ));

      window.setTimeout(_.bind(this.postRender, this));

      return this;
    },

    // Put logic here that should be run after this.$el is added to the DOM
    postRender: function() {
      var user = this.userCourse.get('user');
      var title = _s.sprintf('%s (%s)',
        user.get('name'), this.userCourse.get('term_name'));
      this.$el.tooltip({
        trigger: 'hover',
        title: title
      });
    }
  });


  var CourseCollection = RmcBackbone.Collection.extend({
    model: CourseModel
  });
  CourseCollection.registerCache('course');


  // TODO(mack): it's really UserCourseCollectionView now
  var CourseCollectionView = RmcBackbone.View.extend({
    tagName: 'ol',
    className: 'course-collection',

    initialize: function(attributes) {
      this.courses = attributes.courses;
      this.courses.bind('add', _.bind(this.addCourse, this));
      this.courses.bind('reset', _.bind(this.render, this));
      this.courseViews = [];

      this.canShowAddReview =
        'canShowAddReview' in attributes ? attributes.canShowAddReview : true;
    },

    addCourse: function(course) {
      var courseView = new CourseView({
        canShowAddReview: this.canShowAddReview,
        courseModel: course,
        tagName: 'li'
      });
      this.$el.append(courseView.render().el);
      this.courseViews.push(courseView);
    },

    render: function() {
      this.$el.empty();
      this.courses.each(function(course) {
        this.addCourse(course);
      }, this);

      return this;
    },

    onShow: function() {
      _.each(this.courseViews, function(courseView) {
        courseView.onResize();
      });
    }
  });

  return {
    CourseModel: CourseModel,
    CourseView: CourseView,
    CourseInnerView: CourseInnerView,
    CourseCollection: CourseCollection,
    CourseCollectionView: CourseCollectionView
  };
});
