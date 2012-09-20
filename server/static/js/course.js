define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'review', 'ext/bootstrap', 'user', 'util'],
function(Backbone, $, _, _s, ratings, review, __, user, util) {

  var CourseModel = Backbone.Model.extend({
    defaults: {
      id: 'SCI 238',
      name: 'Introduction to Astronomy omg omg omg',
      rating: 2.5,
      numRatings: 49,
      friendCollection: undefined,
      userReviewModel: undefined,
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
        this.set('ratings', new ratings.RatingCollection(attributes.ratings));
      }
      this.set('userReviewModel',
          new review.UserReviewModel(attributes.userCourse));
      if (!attributes.friendCollection) {
        this.set('friendCollection', user.UserCollection.getSampleCollection());
      }
    }
  });

  var CourseView = Backbone.View.extend({
    className: 'course well',

    initialize: function(options) {
      this.courseModel = options.courseModel;
      var userReviewModel = this.courseModel.get('userReviewModel');
      this.ratingsView = new ratings.RatingsView({
        ratings: this.courseModel.get('ratings'),
        userReviewModel: userReviewModel
      });
      // TODO(david): Get user review data, and don't show or show altered if no
      //     user or user didn't take course.
      this.userReviewView = new review.UserReviewView({
        userReviewModel: userReviewModel,
        courseModel: this.courseModel
      });
    },

    render: function() {
      this.$el.html(
        _.template($('#course-tpl').html(), this.courseModel.toJSON()));

      this.$('.ratings-placeholder').replaceWith(this.ratingsView.render().el);
      this.$('.review-placeholder').replaceWith(
        this.userReviewView.render().el);

      var $target = this.$('.num-friends');
      var numFriends = this.courseModel.get('friendCollection').length;
      // TODO(mack): change back
      var title = _s.sprintf('%d %s taken %s', numFriends,
        util.pluralize(numFriends, 'friend has', 'friends have'),
        this.courseModel.get('id'));
      // TODO(mack): investigate if offset attribute works for popover, need to
      // move popover slightly higher
      $target.popover({
        html: true,
        title: title,
        content: _.bind(this.getCourseFriendsPopoverContent, this),
        trigger: 'hover',
        placement: 'in top'
      });
      // Prevent clicking in the hovercard from expanding/collapsing the course
      // view
      $target.on('click', '.popover', function(evt) {
        return false;
      });

      return this;
    },

    getCourseFriendsPopoverContent: function() {
      if (!this.courseFriendsHovercardView) {
        this.courseFriendsHovercardView = new CourseFriendsHovercardView({
          friendCollection: this.courseModel.get('friendCollection')
        });
      }
      return this.courseFriendsHovercardView.render().$el;
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
      this.$('.expand-section')
        .css('opacity', 0)
        .animate({
          opacity: 1.0
        }, {
          duration: duration,
          queue: false
        })
        .slideDown(duration);

      this.ratingsView.removeBars();
      window.setTimeout(_.bind(function() {
        this.ratingsView.render();
      }, this), duration / 4);
    },

    collapseCourse: function(evt) {
      this.$('.expand-section')
        .stop(/* clearQueue */ true)
        .slideUp(300);
    },

    expandNewReview: function(evt) {
      this.$('.new-review').addClass('new-review-expanded');
    }

  });

  var CourseFriendsHovercardView = Backbone.View.extend({
    tagName: 'ul',
    className: 'friend-collection',

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
      this.$el.tooltip({
        title: this.friendModel.get('name')
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
