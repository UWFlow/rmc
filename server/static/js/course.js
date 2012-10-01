define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'ext/bootstrap', 'util', 'jquery.slide'],
function(RmcBackbone, $, _, _s, ratings, __, util, jqSlide) {

  var CourseModel = RmcBackbone.Model.extend({
    defaults: {
      id: 'SCI 238',
      name: 'Introduction to Astronomy omg omg omg',
      professors: [],
      description: 'This couse will introduce you to the wonderful world' +
        ' of astronomy. Learn about the Milky Way, the Big Bang, and' +
        ' everything in between. Become enthralled in the wonderful' +
        ' world of astronomy.',
      ratings: [{
        name: 'interest',
        count: 10,
        total: 7
      }, {
        name: 'easiness',
        count: 7,
        total: 2
      }],
      user_course_id: undefined,
      friend_user_course_ids: []
    },

    referenceFields: function() {
      // TODO(mack): remove require() call
      var _user_course = require('user_course');
      return {
        'user_course': ['user_course_id', _user_course.UserCourses],
        'friend_user_courses': [ 'friend_user_course_ids', _user_course.UserCourses ]
      };
    },

    initialize: function(attributes) {
      if (attributes.ratings) {
        var ratingsArray = _.map(attributes.ratings, function(rating, name) {
          return _.extend(rating, { name: name });
        });
        this.set('ratings', new ratings.RatingCollection(ratingsArray));
      }
    },

    getProf: function(id) {
      return _.find(this.get('professors'), function(prof) {
        return prof.id === id;
      });
    }
  });

  var CourseView = RmcBackbone.View.extend({
    template: _.template($('#course-tpl').html()),
    className: 'course well',

    initialize: function(attributes) {
      this.courseModel = attributes.courseModel;
      this.ratingBoxView = new ratings.RatingBoxView({
        model: new ratings.RatingModel(this.courseModel.get('overall'))
      });
      this.courseInnerView = new CourseInnerView({
        courseModel: this.courseModel
      });

      var friendUserCourses = this.courseModel.get('friend_user_courses');
      if (friendUserCourses) {
        this.sampleFriendsView = new SampleFriendsView({
          friendUserCourses: friendUserCourses
        });
      }
    },

    render: function() {
      this.$el.html(this.template(this.courseModel.toJSON()));

      this.$('.rating-box-placeholder').replaceWith(
          this.ratingBoxView.render().$el);

      if (this.sampleFriendsView) {
        this.$('.sample-friends-placeholder').replaceWith(
          this.sampleFriendsView.render().$el);
      }

      return this;
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
      this.courseInnerView.animateBars(300 / 4);
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
      var _user_course = require('user_course');
      this.courseModel = attributes.courseModel;
      this.userCourse = this.courseModel.get('user_course');

      if (!this.userCourse && pageData.currentUserId) {
        // TODO(mack): remove require()
        this.userCourse = new _user_course.UserCourse({
          course_id: this.courseModel.get('id'),
          user_id: pageData.currentUserId.$oid
        });
        this.courseModel.set('user_course', this.userCourse);
      }

      this.ratingsView = new ratings.RatingsView({
        ratings: this.courseModel.get('ratings'),
        userCourse: this.userCourse,
        readOnly: true
      });

      if (pageData.currentUserId && this.userCourse.get('user')) {
        // TODO(mack): remove circular dependency
        this.userCourseView = new _user_course.UserCourseView({
          userCourse: this.userCourse,
          courseModel: this.courseModel
        });
      }
    },

    render: function(moreDetails) {
      this.$el.html(this.template({
        more_details: moreDetails,
        course: this.courseModel,
        user_course: this.userCourse
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
    },

    addCourse: function(course) {
      var courseView = new CourseView({
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
