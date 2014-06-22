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

    defaults: {
      title: 'Course comments'
    },

    events: {
      'click .toggle-tips': 'toggleExpand'
    },

    initialize: function(options) {
      this.reviews = options.reviews;
      this.title = this.defaults.title;
      this.course = null;
      if (typeof options.course !== 'undefined') {
        this.title = options.course.id.toUpperCase();
        this.course = options.course;
      }
      if (typeof options.numShown !== 'undefined') {
        this.numShown = options.numShown;
      }
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
      var renderedTips = this.tipsCollectionView.render().$el;
      if (this.title !== this.defaults.title) {
        if (this.numHidden() > 0) {
          var expandFooter = $('<div class="toggle-tips">See ' +
            this.numHidden() + ' more reviews &raquo;</div>');
        } else {
          var expandFooter = $('');
        }

        this.courses = new _course.CourseCollection();
        var courseObjs = [this.course];

        _course.CourseCollection.addToCache(courseObjs);

        _.each(courseObjs, function(courseObj) {
          var id = courseObj.id;
          var course = _course.CourseCollection.getFromCache(id);
          this.courses.add(course);
        }, this);

        var courseCollectionView = new _course.CourseCollectionView({
          courses: this.courses,
          canShowAddReview: true
        });

        this.$('h2').replaceWith(courseCollectionView.render().$el);
      } else {
        var expandFooter = $('');
      }
      this.$('.tips-collection-placeholder').replaceWith(
        renderedTips.add(expandFooter));

      this.$('.review-post').slice(this.numShown)
        .wrapAll('<div class="expanded-tips hide-initial">');

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
        this.$('.toggle-tips')
          .html('See ' + this.numHidden() + ' more tips &raquo;');
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
