define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'user_course', 'ext/bootstrap', 'user', 'util', 'jquery.slide'],
function(RmcBackbone, $, _, _s, ratings, u_c, __, user, util, jqSlide) {

  var CourseModel = RmcBackbone.Model.extend({
    defaults: {
      id: 'SCI 238',
      name: 'Introduction to Astronomy omg omg omg',
      friend_user_courses: new u_c.UserCourses(),
      userCourse: undefined,
      professorNames: ['Eddie Dupont', 'Charlie Clarke', 'Mark Smucker', 'Larry Smith'],
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
      }]
    },

    initialize: function(attributes) {
      if (attributes.ratings) {
        var ratingsArray = _.map(attributes.ratings, function(rating, name) {
          return _.extend(rating, { name: name });
        });
        this.set('ratings', new ratings.RatingCollection(ratingsArray));
      }

      if (attributes.friend_user_courses) {
        var friend_user_courses = new u_c.UserCourses(
            attributes.friend_user_courses);
        this.set('friend_user_courses', friend_user_courses);
      }

      this.set('userCourse', new u_c.UserCourse(attributes.userCourse));
    }
  });

  var CourseView = RmcBackbone.View.extend({
    template: _.template($('#course-tpl').html()),
    className: 'course well',

    initialize: function(options) {
      this.courseModel = options.courseModel;
      this.ratingBoxView = new ratings.RatingBoxView({
        model: new ratings.RatingModel(this.courseModel.get('overall'))
      });
      this.courseInnerView = new CourseInnerView({
        courseModel: this.courseModel
      });
      if (this.courseModel.get('friend_user_courses').length) {
        this.sampleFriendsView = new SampleFriendsView({
          courseModel: this.courseModel
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

    initialize: function(options) {
      this.courseModel = options.courseModel;
      var userCourse = this.courseModel.get('userCourse');
      this.ratingsView = new ratings.RatingsView({
        ratings: this.courseModel.get('ratings'),
        userCourse: userCourse
      });
      // TODO(david): Get user review data, and don't show or show altered if no
      //     user or user didn't take course.
      this.userCourseView = new u_c.UserCourseView({
        userCourse: userCourse,
        courseModel: this.courseModel
      });
    },

    render: function(moreDetails) {
      var context = this.courseModel.toJSON();
      _.extend(context, { more_details: moreDetails });
      this.$el.html(this.template(context));

      this.$('.review-placeholder').replaceWith(
        this.userCourseView.render().el);
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
      this.courseModel = attributes.courseModel;
      this.friendViews = [];
    },

    render: function() {
      var friendUserCourses = this.courseModel.get('friend_user_courses');

      this.$el.html(
        _.template($('#sample-friends-tpl').html(), {
          friend_user_courses: friendUserCourses,
          maxSampleFriends: this.MAX_SAMPLE_FRIENDS
        })
      );

      var sampleFriendCollection = new user.UserCollection(
        friendUserCourses.first(this.MAX_SAMPLE_FRIENDS)
      );
      var friendCollectionView = new FriendCollectionView({
        friendUserCourses: sampleFriendCollection
      });
      this.$('.friend-collection-placeholder').replaceWith(
        friendCollectionView.render().$el);

      var $target = this.$('.remaining-friends');

      var numFriends = friendUserCourses.length;
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
        var friendUserCourses = this.courseModel.get('friend_user_courses');
        var remainingUserCourses = new u_c.UserCourses(
          friendUserCourses.rest(this.MAX_SAMPLE_FRIENDS)
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
        _.template($('#course-friend-tpl').html(), this.userCourse.toJSON())
      );

      window.setTimeout(_.bind(this.postRender, this));

      return this;
    },

    // Put logic here that should be run after this.$el is added to the DOM
    postRender: function() {
      var title = _s.sprintf('%s (%s)',
        this.userCourse.get('user_name'), this.userCourse.get('term_name'));
      this.$el.tooltip({
        trigger: 'hover',
        title: title
      });
    }
  });


  var CourseCollection = RmcBackbone.Collection.extend({
    model: CourseModel
  });


  // TODO(mack): make generic CollectionView
  var CourseCollectionView = RmcBackbone.View.extend({
    tagName: 'ol',
    className: 'course-collection',

    initialize: function(options) {
      this.courseCollection = options.courseCollection;
      this.courseCollection.bind('add', _.bind(this.addCourse, this));
      this.courseCollection.bind('reset', _.bind(this.render, this));
      this.courseViews = [];
    },

    addCourse: function(courseModel) {
      var courseView = new CourseView({
        courseModel: courseModel,
        tagName: 'li'
      });
      this.$el.append(courseView.render().el);
      this.courseViews.push(courseView);
    },

    render: function() {
      this.$el.empty();
      this.courseCollection.each(function(courseModel) {
        this.addCourse(courseModel);
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
