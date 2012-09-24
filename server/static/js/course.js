define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'user_course', 'ext/bootstrap', 'user', 'util', 'jquery.slide'],
function(Backbone, $, _, _s, ratings, u_c, __, user, util, jqSlide) {

  var CourseModel = Backbone.Model.extend({
    defaults: {
      id: 'SCI 238',
      name: 'Introduction to Astronomy omg omg omg',
      friendCollection: undefined,
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

      this.set('userCourse', new u_c.UserCourse(attributes.userCourse));
      if (!attributes.friendCollection) {
        this.set('friendCollection', user.UserCollection.getSampleCollection());
      }
    }
  });

  var CourseView = Backbone.View.extend({
    className: 'course well',

    initialize: function(options) {
      this.courseModel = options.courseModel;
      var userCourse = this.courseModel.get('userCourse');
      this.ratingBoxView = new ratings.RatingBoxView({
        model: new ratings.RatingModel(this.courseModel.get('overall'))
      });
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

    render: function() {
      this.$el.html(
        _.template($('#course-tpl').html(), this.courseModel.toJSON()));

      this.$('.rating-box-placeholder').replaceWith(
          this.ratingBoxView.render().el);
      this.$('.ratings-placeholder').replaceWith(this.ratingsView.render().el);
      this.$('.review-placeholder').replaceWith(
        this.userCourseView.render().el);

      if (this.courseModel.get('friendCollection').length) {
        var sampleFriendsView = new SampleFriendsView({
          courseModel: this.courseModel
        });
        this.$('.sample-friends-placeholder').replaceWith(
          sampleFriendsView.render().$el);
      }

      return this;
    },

    events: {
      // TODO(david): Figure out a nicer interaction without requiring click
      'click .visible-section': 'toggleCourse',
      'focus .new-review-input': 'expandNewReview'
    },

    toggleCourse: function(evt) {
      if (this.$('.expand-section').is(':visible')) {
        this.collapseCourse(evt);
      } else {
        this.expandCourse(evt);
      }
    },

    // XXX TODO(david) FIXME: need to not render expanded HTML until needed
    expandCourse: function(evt) {
      var duration = 300;
      this.$('.expand-section').fancySlide('down', duration);

      this.ratingsView.removeBars();
      window.setTimeout(_.bind(function() {
        this.ratingsView.render();
      }, this), duration / 4);
    },

    collapseCourse: function(evt) {
      this.$('.expand-section').fancySlide('up');
    },

    expandNewReview: function(evt) {
      this.$('.new-review').addClass('new-review-expanded');
    }

  });

  var SampleFriendsView = Backbone.View.extend({
    MAX_SAMPLE_FRIENDS: 3,

    className: 'sample-friends',

    initialize: function(attributes) {
      this.courseModel = attributes.courseModel;
      this.friendViews = [];
    },

    render: function() {
      var friendCollection = this.courseModel.get('friendCollection');

      this.$el.html(
        _.template($('#sample-friends-tpl').html(), {
          friendCollection: friendCollection,
          maxSampleFriends: this.MAX_SAMPLE_FRIENDS
        })
      );

      var sampleFriendCollection = new user.UserCollection(
        friendCollection.first(this.MAX_SAMPLE_FRIENDS)
      );
      var friendCollectionView = new FriendCollectionView({
        friendCollection: sampleFriendCollection
      });
      this.$('.friend-collection-placeholder').replaceWith(
        friendCollectionView.render().$el);

      var $target = this.$('.remaining-friends');

      var numFriends = friendCollection.length;
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
        var friendCollection = this.courseModel.get('friendCollection');
        var remainingFriendCollection = new user.UserCollection(
          friendCollection.rest(this.MAX_SAMPLE_FRIENDS)
        );
        this.friendsHovercardView = new FriendCollectionView({
          friendCollection: remainingFriendCollection
        });
      }
      // TODO(mack): custom width based on number of friends in hovercard
      return this.friendsHovercardView.render().$el;
    }

  });

  var FriendCollectionView = Backbone.View.extend({
    tagName: 'ul',
    className: 'friend-collection clearfix',

    initialize: function(attributes) {
      this.friendCollection = attributes.friendCollection;
      this.friendViews = [];
    },

    render: function() {
      this.$el.html(
        _.template($('#course-friends-hovercard-tpl').html(), {})
      );
      this.friendCollection.each(function(friendModel) {
        this.addFriend(friendModel);
      }, this);

      return this;
    },

    addFriend: function(friendModel) {
      var friendView = new CourseFriendView({
        friendModel: friendModel,
        tagName: 'li'
      });
      this.$el.append(friendView.render().el);
      this.friendViews.push(friendView);
    }

  });

  var CourseFriendView = Backbone.View.extend({
    className: 'friend-pic',

    initialize: function(attributes) {
      this.friendModel = attributes.friendModel;
    },

    render: function() {
      this.$el.html(
        _.template($('#course-friend-tpl').html(), this.friendModel.toJSON())
      );

      window.setTimeout(_.bind(this.postRender, this));

      return this;
    },

    // Put logic here that should be run after this.$el is added to the DOM
    postRender: function() {
      var title = _s.sprintf('%s (%s)',
        this.friendModel.get('name'), this.friendModel.get('lastTermName'));
      this.$el.tooltip({
        trigger: 'hover',
        title: title
      });
    }
  });


  var CourseCollection = Backbone.Collection.extend({
    model: CourseModel
  });


  // TODO(mack): make generic CollectionView
  var CourseCollectionView = Backbone.View.extend({
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
    CourseCollection: CourseCollection,
    CourseCollectionView: CourseCollectionView
  };
});
