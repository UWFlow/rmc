define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'rmc_backbone', 'user', 'jquery.slide', 'review', 'course', 'user_course'],
function($, _, _s, bootstrap, RmcBackbone, user, jqSlide, _review,
  _course, _user_course) {

  // TODO(david): This entire file could probably be merged into review.js once
  //     we have base expandable view class

  var TipsCollectionView = RmcBackbone.CollectionView.extend({
    className: 'tips-collection',

    createItemView: function(model) {
      return new _review.ReviewView({ model: model });
    }
  });

  // TODO(david): Make this fancier. Show more about tip person or something.
  var ExpandableTipsView = RmcBackbone.View.extend({
    className: 'all-tips',
    expanded: false,
    numShown: 3,

    events: {
      'click .toggle-tips': 'toggleExpand'
    },

    initialize: function(options) {
      this.reviews = options.reviews;
      this.title = "Course Comments";
      this.course = null;
      // Possible pageType values are 'prof' and 'course'
      this.pageType = options.pageType;
      options = options || {};
      if (this.pageType === 'prof') {
        this.title = options.course.id.toUpperCase();
        this.course = options.course;
      }
      this.numShown = options.numShown;
      this.tipsCollectionView = new TipsCollectionView({
        collection: this.reviews
      });
      this.template = _.template($('#expandable-tips-tpl').html());
    },

    render: function() {
      this.$el.html(this.template({
        numHidden: this.numHidden(),
        title: this.title
      }));
      var expandFooter = $('');
      var renderedTips = this.tipsCollectionView.render().$el;
      if (this.pageType === 'prof') {
        if (this.numHidden() === 1) {
          var expandFooter = $('<div class="toggle-tips">See ' +
            '1 more review &raquo;</div>');
        } else if (this.numHidden() > 0) {
          var expandFooter = $('<div class="toggle-tips">See ' +
            this.numHidden() + ' more reviews &raquo;</div>');
        }

        this.courses = new _course.CourseCollection([this.course]);

        var courseCollectionView = new _course.CourseCollectionView({
          courses: this.courses,
          canShowAddReview: true
        });

        this.$('.tip-title').replaceWith(courseCollectionView.render().$el);
      } else {
        this.$('.tip-title').text("Course Comments");
      }

      this.$('.tips-collection-placeholder').replaceWith(
        renderedTips.add(expandFooter));
      if (this.pageType === 'prof') {
        this.$('.review-post').slice(this.numShown)
          .wrapAll('<div class="expanded-tips hide-initial">');
      }

      return this;
    },

    numTips: function() {
      return this.reviews.length;
    },

    numHidden: function() {
      return Math.max(0, this.numTips() - this.numShown);
    },

    toggleExpand: function() {
      if (this.expanded) {
        this.$('.expanded-tips').fancySlide('up');
        if (this.numHidden() === 1) {
          this.$('.toggle-tips').html(
              'See ' + this.numHidden() + ' more review &raquo;');
        } else {
          this.$('.toggle-tips').html(
              'See ' + this.numHidden() + ' more reviews &raquo;');
        }
      } else {
        this.$('.expanded-tips').fancySlide('down');
        this.$('.toggle-tips').html('&laquo; Hide reviews');
      }
      this.expanded = !this.expanded;
    }
  });

  return {
    TipsCollectionView: TipsCollectionView,
    ExpandableTipsView: ExpandableTipsView
  };

});
