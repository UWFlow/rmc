define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'jquery.slide', 'rmc_backbone', 'ratings', 'util', 'review'],
function($, _, _s, bootstrap, jqSlide, RmcBackbone, ratings, util, review) {

  var Prof = RmcBackbone.Model.extend({
    defaults: {
      id: 'charles_l.a._clarke',
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
        var kittenNum = util.getKittenNumFromName(attrs.name);
        this.set('pictureUrl',
            '/static/img/kittens/color/' + kittenNum + '.jpg');
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
  var ProfCardView = RmcBackbone.View.extend({
    className: 'prof-card',

    initialize: function() {
      this.template = _.template($('#prof-card-tpl').html());
    },

    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  var ProfCollection = RmcBackbone.Collection.extend({
    model: Prof,

    // TODO(david): Allow changing sort/filter options
    comparator: function(prof) {
      // The professors need not be sorted for the collection cache
      if (!prof.get('overall')) {
        return 0;
      }
      return -prof.get('overall').get('count');
    }
  });
  ProfCollection.registerCache('prof');

  // TODO(david): Need base expandable collection view
  var ExpandableProfView = RmcBackbone.View.extend({
    firstExpanded: false,
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
        subject: 'professor'
      });

      this.template = _.template($('#prof-expandable-reviews-tpl').html());
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
        this.profReviewCollectionView.render(true).el);

      return this;
    },

    numReviews: function() {
      return this.reviews.length;
    },

    numHidden: function() {
      return Math.max(this.numReviews() - this.numShown);
    },

    toggleExpand: function() {
      if (!this.firstExpanded) {
        this._loadReviews();
      } else if (this.expanded) {
        this._collapseReviews();
      } else {
        this._expandReviews();
      }
    },

    _loadReviews: function() {
      this.firstExpanded = true;
      this.$('.toggle-reviews').text('Loading...');
      window.setTimeout(_.bind(function() {
        this.profReviewCollectionView.render(false);

        this.$('.review-post').slice(this.numShown)
          .wrapAll('<div class="expanded-reviews hide-initial">');

        this._expandReviews();
      }, this), 100);
    },

    _collapseReviews: function() {
      var profCardTop = this.$('.expandable-prof').offset().top;
      var navBarHeight = $("#site-nav").height();
      var margin = 16;

      $('html,body').animate({
        scrollTop: profCardTop - navBarHeight - margin
      }, 300);

      this.$('.expanded-reviews').fancySlide('up');
      this.$('.toggle-reviews')
        .html('See ' + this.numHidden() + ' more ' +
              util.pluralize(this.numHidden(), 'review') + ' &raquo;');
      this.expanded = false;
    },

    _expandReviews: function() {
      this.$('.expanded-reviews').fancySlide('down');
      this.$('.toggle-reviews').html('&laquo; Hide reviews');
      this.expanded = true;
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
