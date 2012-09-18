define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'review', 'ext/bootstrap'],
function(Backbone, $, _, _s, ratings, review, __) {

  var CourseModel = Backbone.Model.extend({
    defaults: {
      id: 'SCI 238',
      name: 'Introduction to Astronomy omg omg omg',
      rating: 2.5,
      numRatings: 49,
      numFriendsTook: 2,
      userReviewModel: null,
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
      if (!attributes.userReviewModel) {
        this.set('userReviewModel', new review.UserReviewModel());
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

      return this;
    },

    events: {
      'mouseenter .friend-name': 'showCourseFriendsHovercard',
      // TODO(david): Figure out a nicer interaction without requiring click
      'click .visible-section': 'toggleCourse',
      'focus .new-review-input': 'expandNewReview'
    },

    showCourseFriendsHovercard: function(evt) {
      var hovercardView = new CourseFriendsHovercardView({
        courseModel: this.courseModel,
        $target: $(evt.currentTarget)
      });
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
    initialize: function(attributes) {
      this.$target = attributes.$target;
      this.courseModel = attributes.courseModel;
    },

    render: function() {
      this.$target.popover({
        html: true,
        title: 'Friends',
        content: _.bind(this.getPopoverContent, this),
        trigger: 'manual',
        placement: 'top'
      }).hover(function(evt) {
        $(this).popover('show');
        evt.preventDefault();
      });

      return this;
    },

    getPopoverContent: function() {
      this.$el.html(
        _.template($('#course-friends-hovercard-tpl').html(), this.courseModel.toJSON())
      );
      return this.$el;
    },

    // Override remove to also destroy the popover
    remove: function() {
      this.__super__.remove.apply(this, arguments);
      this.$target.popover('destroy');
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
