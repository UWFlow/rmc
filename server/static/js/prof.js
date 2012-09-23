define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'ext/backbone', 'jquery.slide', 'base_views', 'ratings', 'util'],
function($, _, _s, bootstrap, Backbone, jqSlide, baseViews, ratings, util) {

  var Prof = Backbone.Model.extend({
    defaults: {
      name: 'Charles L.A. Clarke',
      email: 'charles.clarke@uwaterloo.ca',
      phone: '519-888-4567 x35241',
      office: 'DC 2506',
      department: 'School of Computer Science',
      pictureUrl: ''
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

  // TODO(david): This might just be a user-course model
  var ProfReview = Backbone.Model.extend({
    defaults: {
      name: 'Larry Smith',
      passion: 5,
      clarity: 3,
      overall: 6,
      comment: 'Was great!!!!!!!!!!!!!!!!'
    }
  });

  var ProfReviewView = Backbone.View.extend({
    className: 'prof-review',
    template: _.template($('#prof-review-tpl').html()),

    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  var ProfReviewCollection = Backbone.Collection.extend({
    model: ProfReview
  });

  var ProfReviewCollectionView = baseViews.CollectionView.extend({
    className: 'prof-review-collection',

    createItemView: function(model) {
      return new ProfReviewView({ model: model });
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

      this.reviews = options.reviews;
      this.profReviewCollectionView = new ProfReviewCollectionView({
        collection: this.reviews
      });

      // TODO(david): Removed mocked data
      var ratingsCollection = new ratings.RatingCollection([
        { name: 'interest', count: 20, total: 15 },
        { name: 'easiness', count: 40, total: 37 }
      ]);
      this.ratingsView = new ratings.RatingsView({
        ratings: ratingsCollection,
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
      this.$('.aggregate-ratings-placeholder').replaceWith(
        this.ratingsView.render().el);

      // Professor reviews
      this.$('.reviews-collection-placeholder').replaceWith(
        this.profReviewCollectionView.render().el);

      this.$('.prof-review').slice(this.numShown)
        .wrapAll('<div class="expanded-reviews hide-initial">');

      return this;
    },

    numReviews: function() {
      return this.reviews.length;
    },

    numHidden: function() {
      return this.numReviews() - this.numShown;
    },

    toggleExpand: function() {
      if (this.expanded) {
        this.$('.expanded-reviews').fancySlide('up');
        this.$('.toggle-reviews')
          .html('See ' + this.numHidden() + ' more reviews &raquo;');
      } else {
        this.$('.expanded-reviews').fancySlide('down');
        this.$('.toggle-reviews').html('&laquo; Hide reviews');
      }
      this.expanded = !this.expanded;
    }
  });

  var ProfCollectionView = baseViews.CollectionView.extend({
    className: 'prof-collection',

    initialize: function(options) {

    },

    createItemView: function(model) {
      return new ExpandableProfView({
        model: model
      });
    }
  });

  return {
    Prof: Prof,
    ProfCardView: ProfCardView,
    ProfReview: ProfReview,
    ProfReviewCollection: ProfReviewCollection,
    ProfReviewCollectionView: ProfReviewCollectionView,
    ExpandableProfView: ExpandableProfView
  };

});
