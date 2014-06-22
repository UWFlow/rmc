define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'util', 'ext/bootstrap'],
function(RmcBackbone, $, _, _s, util, _bootstrap) {

  // TODO(david): Maybe this should be in util
  var adjectiveMap = {
    'interest': 'Liked it',
    'easiness': 'easy',
    'usefulness': 'useful',
    'clarity': 'clear',
    'passion': 'engaging',
    '': ''
  };

  // TODO(david): Refactor all the row-fluid to use an actual class name

  // A rating of a single metric
  // TODO(david): Fix this to just be count + rating (instead of total)
  var RatingModel = RmcBackbone.Model.extend({
    defaults: {
      name: null,
      rating: null,
      count: null
    },

    getDisplayName: function() {
      return adjectiveMap[this.get('name')];
    },

    getAverage: function() {
      return this.get('count') ? this.get('rating') : 0;
    },

    getPercent: function() {
      return this.getAverage() * 100;
    },

    getDisplayRating: function(placeholder) {
      return util.getDisplayRating(this.get('rating'), this.get('count'),
              placeholder) + (this.get('count') ? '%' : '');
    },

    getLikes: function() {
      return Math.round(this.get('rating') * this.get('count'));
    },

    getDislikes: function() {
      return this.get('count') - this.getLikes();
    }
  });

  var RatingCollection = RmcBackbone.Collection.extend({
    model: RatingModel,

    getRating: function(name) {
      return this.where({ name: name })[0];
    }
  });

  var RatingsView = RmcBackbone.View.extend({
    initialize: function(options) {
      this.ratings = options.ratings;
      this.userCourse = options.userCourse;
      this.subject = options.subject;
      this.template = _.template($('#ratings-tpl').html());
    },

    render: function() {
      var ratings = this.ratings;
      this.$el.html(this.template({
        ratings: ratings,
        subject: this.subject
      }));

      this.$('[title]').tooltip();

      // Set the width here instead of in the template for animations
      this.$('.shown-rating .rating-progress').each(function(i, elem) {
        var percent = ratings.at(i).getPercent();
        $(elem).find('.positive').css('width', percent + '%');
        if (ratings.at(i).get('count') === 0) {
          $(elem).hide();
        }
      });

      return this;
    },

    removeBars: function() {
      this.$('.bar').remove();
    }

  });

  var RatingBoxView = RmcBackbone.View.extend({
    className: 'rating-box',

    initialize: function() {
      this.template = _.template($('#rating-box-tpl').html());
    },

    render: function() {
      this.$el
        .html(this.template(this.model.toJSON()))
        .tooltip({
          title: this.model.getLikes() + ' likes, ' + this.model.getDislikes() +
              ' dislikes',
          placement: 'top'
        });
      return this;
    }
  });

  var RatingChoice = RmcBackbone.Model.extend({
    defaults: {
      name: '',
      rating: null
    },

    getAdjective: function() {
      return adjectiveMap[this.get('name')];
    }
  });

  var RatingChoiceView = RmcBackbone.View.extend({
    className: 'rating-choice',

    initialize: function(options) {
      this.model.on('change:rating', _.bind(this.setStateFromRating, this));
      this.template = _.template($('#binary-rating-tpl').html());
      if (options.voting) {
        this.template = _.template($('#voting-tpl').html());
      }
      if (options.readOnly) {
        this.readOnly = true;
      }
    },

    render: function() {
      this.$el.html(this.template({
        'name': adjectiveMap[this.model.get('name')],
        'read_only': this.readOnly
      }));
      if (this.readOnly) {
        this.$('.btn').prop('disabled', true);
      }

      this.setStateFromRating();
      if (this.options.voting) {
        this.$('.btn').tooltip();
      }
      return this;
    },

    events: {
      'click .btn': 'onClick'
    },

    onClick: function(evt) {
      if (this.readOnly) {
        return;
      }
      var $btn = $(evt.currentTarget);
      var rating = this.model.get('rating');
      var chosen = $btn.hasClass('yes-btn') ? 1 : 0;
      if (rating === chosen) {
        this.model.set('rating', null);
      } else {
        this.model.set('rating', chosen);
      }
      evt.stopPropagation();
    },

    setStateFromRating: function() {
      var rating = this.model.get('rating');
      var $yesButton = this.$('.yes-btn');
      var $noButton = this.$('.no-btn');
      $yesButton.removeClass('active btn-success');
      $noButton.removeClass('active btn-danger');
      if (rating === 1) {
        $yesButton.addClass('active btn-success');
      } else if (rating === 0) {
        $noButton.addClass('active btn-danger');
      }
    }
  });

  var RatingChoiceCollection = RmcBackbone.Collection.extend({
    model: RatingChoice,

    hasRated: function() {
      return this.any(function(rating) {
        return _.isNumber(rating.get('rating'));
      });
    },

    allRated: function() {
      return this.all(function(rating) {
        return _.isNumber(rating.get('rating'));
      });
    }
  });

  var RatingChoiceCollectionView = RmcBackbone.CollectionView.extend({
    createItemView: function(model) {
      return new RatingChoiceView(_.extend({ model: model }, this.options));
    }
  });

  return {
    RatingModel: RatingModel,
    RatingCollection: RatingCollection,
    RatingsView: RatingsView,
    RatingBoxView: RatingBoxView,
    RatingChoice: RatingChoice,
    RatingChoiceView: RatingChoiceView,
    RatingChoiceCollection: RatingChoiceCollection,
    RatingChoiceCollectionView: RatingChoiceCollectionView
  };

});
