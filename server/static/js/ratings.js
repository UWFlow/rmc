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

  var NUM_SEGMENTS = 5;
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

    getDisplayRating: function() {
      return util.getDisplayRating(this.get('rating'), this.get('count')) +
          (this.get('count') ? '%' : '');
    },

    // TODO(david): This shouldn't be here. Refactor this away.
    getClass: function() {
      return {
        'interest': 'progress-info',
        'easiness': 'progress-warning',
        'passion': 'progress-danger',
        'clarity': 'progress-success'
      }[this.get('name')];
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
    template: _.template($('#ratings-tpl').html()),

    initialize: function(options) {
      this.ratings = options.ratings;
      this.userCourse = options.userCourse;
      this.subject = options.subject;
    },

    render: function() {
      var ratings = this.ratings;
      this.$el.html(this.template({ ratings: ratings, subject: this.subject }));

      this.$('[title]').tooltip();

      // Set the width here instead of in the template for animations
      this.$('.shown-rating .bar').each(function(i, elem) {
        $(elem).css('width', ratings.at(i).getPercent() + '%');
      });

      return this;
    },

    removeBars: function() {
      this.$('.bar').remove();
    }

  });

  var RatingBoxView = RmcBackbone.View.extend({
    template: _.template($('#rating-box-tpl').html()),
    className: 'rating-box badge badge-inverse',

    render: function() {
      this.$el
        .html(this.template(this.model.toJSON()))
        .tooltip({
          title: this.model.getLikes() + ' likes, ' + this.model.getDislikes() +
              ' dislikes'
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
    template: _.template($('#binary-rating-tpl').html()),
    className: 'rating-choice',

    initialize: function(options) {
      this.model.on('change:rating', _.bind(this.setStateFromRating, this));
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
      if (this.readOnly) return;
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
    model: RatingChoice
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
