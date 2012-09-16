define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string'],
function(Backbone, $, _, _s) {

  var NUM_SEGMENTS = 5;

  // A rating of a single metric
  var RatingModel = Backbone.Model.extend({
    defaults: {
      name: 'interest',
      count: 10,
      total: 7
    },

    getAverage: function() {
      return this.get('total') / Math.max(1, this.get('count'));
    },

    getPercent: function() {
      return this.getAverage() * 100;
    },

    getDisplayRating: function() {
      return _s.sprintf("%.1f", this.getAverage() * NUM_SEGMENTS);
    },

    // TODO(david): This shouldn't be here. Refactor this away.
    getClass: function() {
      return {
        'interest': 'progress-info',
        'easiness': 'progress-warning'
      }[this.get('name')];
    }
  });

  var RatingCollection = Backbone.Collection.extend({
    model: RatingModel,

    getNameAt: function(index) {
      return this.at(index).get('name');
    }
  });

  var RatingsView = Backbone.View.extend({

    events: {
      'mouseenter .rating-progress': 'onRatingHover'
    },

    initialize: function(options) {
      this.ratings = options.ratings;
      this.userReviewModel = options.userReviewModel;
    },

    render: function() {
      var ratings = this.ratings;
      this.$el.html(_.template($('#ratings-tpl').html(), { ratings: ratings }));

      // Set the width here instead of in the template for animations
      this.$('.shown-rating .bar').each(function(i, elem) {
        $(elem).css('width', ratings.at(i).getPercent() + '%');
      });

      this.setUserRatings();

      return this;
    },

    setUserRatings: function() {
      var self = this;
      this.$('.input-rating').each(function(i, inputRating) {
        var name = self.ratings.getNameAt(i);
        var userRating = self.userReviewModel.getRating(name);
        var value = userRating ? userRating * NUM_SEGMENTS : 0;
        self.selectRating(inputRating, value);
      });
    },

    removeBars: function() {
      this.$('.bar').remove();
    },

    // TODO(david): Refactor to use single model+view for each rating
    onRatingHover: function(evt) {
      this.setUserRatings();

      $target = $(evt.currentTarget);
      var $rowElem = $target.closest('.row-fluid');
      var value = $target.index();
      this.selectRating($rowElem.find('.input-rating'), value);

      $rowElem.find('.rating-num-span').text(value + 1);
    },

    selectRating: function(inputRatingElem, value) {
      $(inputRatingElem).find('.rating-bar').each(function(i, elem) {
        $(elem).toggleClass('bar', i <= value);
      });
    }

  });

  return {
    RatingModel: RatingModel,
    RatingCollection: RatingCollection,
    RatingsView: RatingsView
  };

});
