define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'ext/backbone', 'jquery.slide', 'base_views'],
function($, _, _s, bootstrap, Backbone, jqSlide, baseViews) {

  var Prof = Backbone.Model.extend({
    defaults: {
      name: 'Charles L.A. Clarke',
      email: 'charles.clarke@uwaterloo.ca',
      phone: '519-888-4567 x35241',
      office: 'DC 2506',
      department: 'School of Computer Science',
      pictureUrl: 'http://placekitten.com/400/400'
    }
  });

  // TODO(david): Convert other backbone views to pre-compile templates
  var ProfCardView = Backbone.View.extend({
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
    },

    render: function() {
      this.$el.html(this.template({
        numHidden: this.numHidden()
      }));

      this.$('.prof-card-placeholder').replaceWith(this.profView.render().el);

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

  return {
    Prof: Prof,
    ProfCardView: ProfCardView,
    ProfReview: ProfReview,
    ProfReviewCollection: ProfReviewCollection,
    ProfReviewCollectionView: ProfReviewCollectionView,
    ExpandableProfView: ExpandableProfView
  };

});
