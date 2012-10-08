define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'ext/bootstrap', 'util', 'jquery.slide', 'prof'],
function(RmcBackbone, $, _, _s, ratings, __, util, jqSlide, _prof) {

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
      professor_ids: []
    },

    referenceFields: function() {
      // TODO(mack): remove require() call
      var _user_course = require('user_course');
      return {
        'user_course': ['user_course_id', _user_course.UserCourses],
        'profile_user_course': ['profile_user_course_id', _user_course.UserCourses],
        'friend_user_courses': [ 'friend_user_course_ids', _user_course.UserCourses ],
        'professors': [ 'professor_ids', _prof.ProfCollection ]
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
    },

    getProf: function(id) {
      return this.get('professors').find(function(prof) {
        return prof.id === id;
      });
    },

    getOverallRating: function() {
      if (this.has('overall')) {
        return this.get('overall');
      } else {
        var isOverall = function(rating) { return rating.name === 'interest'; };
        return _.find(attributes.ratings, isOverall);
      }
    }
  });

  var CourseView = RmcBackbone.View.extend({
    template: _.template($('#course-tpl').html()),
    className: 'course well',

    initialize: function(attributes) {
      this.courseModel = attributes.courseModel;
      this.userCourse = this.courseModel.get('user_course');
      // TODO(mack): Might not always be appropriate to just fetch
      // profileUserCourse like this since it's only gettable from
      // profile page
      this.profileUserCourse = this.courseModel.get('profile_user_course');

      if (this.userCourse) {
        // TODO(mack): ensure that save actually is save of review
        this.userCourse.bind('sync', _.bind(function(model, response, options) {
          this.onSaveUserReview();
        }, this));
      }

      this.canShowAddReview =
        'canShowAddReview' in attributes ? attributes.canShowAddReview : true;

      var overallRating = this.courseModel.getOverallRating();
      this.ratingBoxView = new ratings.RatingBoxView({ model: overallRating });

      if (this.canShowAddReview && this.userCourse) {
        this.votingView = new ratings.RatingChoiceView({
          model: this.userCourse.getOverallRating(),
          voting: true,
          className: 'voting'
        });
      }

      this.courseInnerView = new CourseInnerView({
        courseModel: this.courseModel,
        userCourse: this.userCourse,
        canShowAddReview: this.canShowAddReview
      });

      var friendUserCourses = this.courseModel.get('friend_user_courses');
      if (friendUserCourses) {
        this.sampleFriendsView = new SampleFriendsView({
          friendUserCourses: friendUserCourses
        });
      }
    },

    onSaveUserReview: function() {
      this.$('.current-user-ribbon').addClass('reviewed');
    },

    render: function() {
      this.$el.html(this.template({
        course: this.courseModel.toJSON(),
        user_course: this.userCourse && this.userCourse.toJSON(),
        profile_user_course: this.profileUserCourse && this.profileUserCourse.toJSON(),
        other_profile: pageData.ownProfile === false
      }));

      var title = '';
      var termTookName = '';

      if (this.userCourse) {
        termTookName = this.userCourse.get('term_name');
        if (this.userCourse.get('has_reviewed')) {
          title = _s.sprintf('Taken in %s. Thanks for reviewing!',
              termTookName);
        } else {
          title = _s.sprintf('Taken in %s. Please review?', termTookName);
        }
        this.$('.current-user-ribbon').tooltip({
          title: title,
          placement: 'top'
        });

        if (this.canShowAddReview) {
          this.$('.voting-placeholder').replaceWith(this.votingView.render().el);
        }
      }

      if (this.otherProfile) {

        var user = this.profileUserCourse.get('user');
        termTookName = this.profileUserCourse.get('term_name');

        if (this.profileUserCourse.get('has_reviewed')) {
          // TODO(mack): fix terrible wording
          title = _s.sprintf('Taken by %s in %s. Has been reviewed.',
              user.get('first_name'), termTookName);
        } else {
          title = _s.sprintf('Taken by %s in %s',
              user.get('first_name'), termTookName);
        }

        this.$('.profile-user-ribbon').tooltip({
          title: title,
          placement: 'top'
        });
      }

      this.$('.rating-box-placeholder').replaceWith(
          this.ratingBoxView.render().$el);

      if (this.sampleFriendsView) {
        this.$('.sample-friends-placeholder').replaceWith(
          this.sampleFriendsView.render().$el);
      }

      if (!this.resizeBounded) {
        $(window).on('resize', _.bind(this.onResize, this));
        this.resizeBounded = true;
      }
      _.defer(_.bind(this.onResize, this));

      return this;
    },

    onResize: function() {
      // TODO(david): Try to do this in CSS
      var codeWidth = this.$('.course-code').width();
      var barWidth = this.$('.visible-section').width();
      this.$('.course-name').width(Math.min(300, barWidth - 270 - codeWidth));
    },

    events: {
      // TODO(david): Figure out a nicer interaction without requiring click
      'click .visible-section': 'toggleCourse',
      'focus .new-review-input': 'expandNewReview'
    },

    toggleCourse: function(evt) {
      if (this.$('.course-inner').is(':visible')) {
        this.collapseCourse(evt);
      } else {
        this.expandCourse(evt);
      }
    },

    expandCourse: function(evt) {
      if (!this.innerRendered) {
        this.innerRendered = true;

        // TODO(david): Neaten this jQuery
        var $inner = this.courseInnerView.render(/* moreDetails */ true).$el;
        $inner.addClass('hide-initial');
        this.$('.course-inner-placeholder').replaceWith($inner);
      }

      this.courseInnerView.$el.fancySlide('down', 300);
      this.courseInnerView.animateBars(0);
    },

    collapseCourse: function(evt) {
      this.$('.course-inner').fancySlide('up');
    },

    expandNewReview: function(evt) {
      this.$('.new-review').addClass('new-review-expanded');
    }
  });

  // TODO(david): Refactor things to use implicit "model" on views
  var CourseInnerView = RmcBackbone.View.extend({
    template: _.template($('#course-inner-tpl').html()),
    className: 'course-inner',

    initialize: function(attributes) {
      this.courseModel = attributes.courseModel;
      this.userCourse = attributes.userCourse;
      this.canShowAddReview =
        'canShowAddReview' in attributes ? attributes.canShowAddReview : true;

      this.ratingsView = new ratings.RatingsView({
        ratings: this.courseModel.get('ratings'),
        userCourse: this.userCourse,
        subject: 'course'
      });

      if (this.canShowAddReview && this.userCourse) {
        // TODO(david): Get user review data, and don't show or show altered if no
        //     user or user didn't take course.
        // TODO(mack): remove circular dependency
        var _user_course = require('user_course');
        this.userCourseView = new _user_course.UserCourseView({
          userCourse: this.userCourse,
          courseModel: this.courseModel
        });
      }
    },

    render: function(moreDetails) {
      this.$el.html(this.template({
        more_details: moreDetails,
        course: this.courseModel.toJSON(),
        user_course: this.userCourse,
        can_show_add_review: this.canShowAddReview
      }));

      if (this.userCourseView) {
        this.$('.review-placeholder').replaceWith(
          this.userCourseView.render().el);
      }

      this.$('.ratings-placeholder').replaceWith(this.ratingsView.render().el);

      return this;
    },

    animateBars: function(pause) {
      pause = pause === undefined ? 0 : pause;
      this.ratingsView.removeBars();

      window.setTimeout(_.bind(function() {
        this.ratingsView.render();
      }, this), pause);

      return this;
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
