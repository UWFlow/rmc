define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'util'],
function(Backbone, $, _, _s, util) {

  var NUM_SEGMENTS = 5;
  // TODO(david): Refactor all the row-fluid to use an actual class name

  // A rating of a single metric
  // TODO(david): Fix this to just be count + rating (instead of total)
  var RatingModel = Backbone.Model.extend({
    defaults: {
      name: 'interest',
      rating: 0.66,
      count: 7
    },

    getDisplayName: function() {
      return util.capitalize(this.get('name'));
    },

    getAverage: function() {
      return util.skewRating(this.get('rating'), this.get('count'));
    },

    getPercent: function() {
      return this.getAverage() * 100;
    },

    getDisplayRating: function() {
      return util.getDisplayRating(this.get('rating'), this.get('count'));
    },

    // TODO(david): This shouldn't be here. Refactor this away.
    getClass: function() {
      return {
        'interest': 'progress-info',
        'easiness': 'progress-warning',
        'passion': 'progress-danger',
        'clarity': 'progress-success'
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
      'mouseenter .rating-progress': 'onRatingHover',
      'mouseleave .input-rating': 'setUserRatings',
      'click .rating-progress': 'onRatingClick'
    },

    initialize: function(options) {
      this.ratings = options.ratings;
      this.userCourse = options.userCourse;
      this.editOnly = options.editOnly;
      this.readOnly = options.readOnly;

      if (!this.readOnly) {
        this.userCourse.on('change', this.setUserRatings, this);
      }
    },

    render: function() {
      var ratings = this.ratings;
      this.$el.html(_.template($('#ratings-tpl').html(), {
        ratings: ratings,
        editOnly: this.editOnly,
        readOnly: this.readOnly
      }));

      // Set the width here instead of in the template for animations
      this.$('.shown-rating .bar').each(function(i, elem) {
        $(elem).css('width', ratings.at(i).getPercent() + '%');
      });

      this.setUserRatings();

      return this;
    },

    setUserRatings: function() {
      if (this.readOnly) {
        return;
      }

      var self = this;
      this.$('.input-rating').each(function(i, inputRating) {
        var name = self.ratings.getNameAt(i);
        var userRating = self.userCourse.getRating(name);
        var value = userRating ? userRating * NUM_SEGMENTS : 0;
        self.selectRating(inputRating, value);
      });
    },

    removeBars: function() {
      this.$('.bar').remove();
    },

    // TODO(david): Refactor to use single model+view for each rating
    onRatingHover: function(evt) {
      if (this.readOnly) {
        return;
      }

      this.setUserRatings();

      var $target = $(evt.currentTarget);
      var $rowElem = $target.closest('.row-fluid');
      var value = $target.index() + 1;
      this.selectRating($rowElem.find('.input-rating'), value);
    },

    selectRating: function(inputRatingElem, value) {
      var numberValue = value === 0 ? '' : value;
      $(inputRatingElem)
        .find('.rating-bar').each(function(i, elem) {
          $(elem).toggleClass('bar', i < value).css('opacity', '');
        })
        .closest('.row-fluid').find('.input-rating-num').text(numberValue);
    },

    onRatingClick: function(evt) {
      if (this.readOnly) {
        return;
      }
      var $target = $(evt.currentTarget);
      var index = $target.closest('.row-fluid').index();
      var name = this.ratings.getNameAt(index);
      var value = ($target.index() + 1) / NUM_SEGMENTS;
      this.userCourse.setRating(name, value);
      $target.parent().find('.bar').css('opacity', 1.0);
    }

  });

  var RatingBoxView = Backbone.View.extend({
    template: _.template($('#rating-box-tpl').html()),

    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  return {
    RatingModel: RatingModel,
    RatingCollection: RatingCollection,
    RatingsView: RatingsView,
    RatingBoxView: RatingBoxView
  };

});
