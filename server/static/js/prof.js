define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'ext/backbone', 'jquery.slide', 'rmc_backbone', 'ratings', 'util', 'comment', 'review'],
function($, _, _s, bootstrap, Backbone, jqSlide, RmcBackbone, ratings, util,
    comment, review) {

  var Prof = Backbone.Model.extend({
    defaults: {
      name: 'Charles L.A. Clarke',
      email: 'charles.clarke@uwaterloo.ca',
      phone: '519-888-4567 x35241',
      office: 'DC 2506',
      department: 'School of Computer Science',
      pictureUrl: '',
      course_ratings: [],
      reviews: null
    },

    initialize: function(attributes) {
      // TODO(david): Use some other instructional placeholder
      if (!attributes || !attributes.pictureUrl) {
        var attrs = attributes ? attributes : this.defaults;
        var size = [
            util.getHashCode(attrs.name) % 20 + 140,
            util.getHashCode(attrs.email) % 20 + 140
        ];
        this.set('pictureUrl',
            'http://placekitten.com/' + size[0] + '/' + size[1]);
      }

      if (attributes && attributes.course_ratings) {
        var coll = new ratings.RatingCollection(attributes.course_ratings);
        var overall = coll.where({ name: 'overall' })[0];
        this.set('overall', overall);
        coll.remove(overall);
        this.set('ratings', coll);
      } else {
        this.set('ratings', new ratings.RatingCollection());
      }

      if (attributes && attributes.course_reviews) {
        var reviews = new review.ReviewCollection(attributes.course_reviews);
        this.set('reviews', reviews);
      } else {
        this.set('reviews', new review.ReviewCollection());
      }
    }
  });

  // TODO(david): Convert other backbone views to pre-compile templates
  var ProfCardView = Backbone.View.extend({
    className: 'prof-card',
    template: _.template($('#prof-card-tpl').html()),

    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  var ProfCollection = Backbone.Collection.extend({
    model: Prof,

    // TODO(david): Allow changing sort/filter options
    comparator: function(prof) {
      return -prof.get('overall').get('count');
    }
  });

  // TODO(david): Need base expandable collection view
  var ExpandableProfView = Backbone.View.extend({
    template: _.template($('#prof-expandable-reviews-tpl').html()),
    expanded: false,
    numShown: 1,

    events: {
      'click .toggle-reviews': 'toggleExpand'
    },

    initialize: function(options) {
      this.prof = options.prof;
      this.profView = new ProfCardView({
        model: this.prof
      });

      // Reviews
      this.reviews = options.reviews;
      this.profReviewCollectionView = new review.ReviewCollectionView({
        collection: this.reviews
      });

      // Rating info
      this.ratingBoxView = new ratings.RatingBoxView({
        model: this.prof.get('overall')
      });
      this.ratingsView = new ratings.RatingsView({
        ratings: this.prof.get('ratings'),
        readOnly: true
      });
    },

    render: function() {
      this.$el.html(this.template({
        numHidden: this.numHidden()
      }));

      // Professor business card
      this.$('.prof-card-placeholder').replaceWith(this.profView.render().el);

      // Aggregate rating
      this.$('.rating-box-placeholder').replaceWith(
          this.ratingBoxView.render().el);
      this.$('.aggregate-ratings-placeholder').replaceWith(
        this.ratingsView.render().el);

      // Professor reviews
      this.$('.reviews-collection-placeholder').replaceWith(
        this.profReviewCollectionView.render().el);

      // TODO(david): Performance: delay rendering of hidden reviews
      this.$('.review-post').slice(this.numShown)
        .wrapAll('<div class="expanded-reviews hide-initial">');

      return this;
    },

    numReviews: function() {
      return this.reviews.length;
    },

    numHidden: function() {
      return Math.max(this.numReviews() - this.numShown);
    },

    toggleExpand: function() {
      if (this.expanded) {
        this.$('.expanded-reviews').fancySlide('up');
        this.$('.toggle-reviews')
          .html('See ' + this.numHidden() + ' more ' +
              util.pluralize(this.numHidden(), 'review') + ' &raquo;');
      } else {
        this.$('.expanded-reviews').fancySlide('down');
        this.$('.toggle-reviews').html('&laquo; Hide reviews');
      }
      this.expanded = !this.expanded;
    }
  });

  var ProfCollectionView = RmcBackbone.CollectionView.extend({
    className: 'prof-collection',

    createItemView: function(model) {
      return new ExpandableProfView({
        prof: model,
        reviews: model.get('reviews')
      });
    }
  });

  return {
    Prof: Prof,
    ProfCardView: ProfCardView,
    ProfCollection: ProfCollection,
    ExpandableProfView: ExpandableProfView,
    ProfCollectionView: ProfCollectionView
  };

});
