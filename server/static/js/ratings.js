define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string'],
function(Backbone, $, _, _s) {

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
      return _s.sprintf("%.1f", this.getAverage() * 5);
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
    model: RatingModel
  });

  var RatingsView = Backbone.View.extend({

    events: {
      'mouseenter .rating-progress': 'onRatingHover'
    },

    render: function() {
      var ratings = this.collection;
      this.$el.html(_.template($('#ratings-tpl').html(), { ratings: ratings }));

      // Set the width here instead of in the template for animations
      this.$('.shown-rating .bar').each(function(i, elem) {
        $(elem).css('width', ratings.at(i).getPercent() + '%');
      });

      return this;
    },

    removeBars: function() {
      this.$('.bar').remove();
    },

    // TODO(david): Refactor to use single model+view for each rating
    onRatingHover: function(evt) {
      $target = $(evt.currentTarget);
      var $rowElem = $target.parents('.row-fluid');
      var value = $target.index();
      this.selectRating($rowElem, value);

      $rowElem.find('.rating-num-span').text(value + 1);

      // Clear all other stars
      var self = this;
      $target.parents('.ratings')
        .find('.row-fluid').not($rowElem).each(function(i, elem) {
          self.resetRating(elem);
        });
    },

    selectRating: function(rowElem, value) {
      $(rowElem).find('.input-rating .rating-progress').each(function(i, elem) {
        $('.rating-bar', elem).toggleClass('bar', i <= value);
      });
    },

    resetRating: function(parentElem) {
      // TODO(david): Get data from server and save locally
      // TODO(david): Refactor HTML/CSS so numbers are reset
      $(parentElem)
        .find('.input-rating .rating-progress').each(function(i, elem) {
          $('.rating-bar', elem).removeClass('bar');
        }).end()
        .find('.rating-num-span').text(0);
    }

  });

  return {
    RatingModel: RatingModel,
    RatingCollection: RatingCollection,
    RatingsView: RatingsView
  };

});
