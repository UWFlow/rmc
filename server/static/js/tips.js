define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'rmc_backbone', 'user', 'jquery.slide', 'review'],
function($, _, _s, bootstrap, RmcBackbone, user, jqSlide, _review) {

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

    events: {
      'click .toggle-tips': 'toggleExpand'
    },

    initialize: function(options) {
      this.reviews = options.reviews;
      this.tipsCollectionView = new TipsCollectionView({
        collection: this.reviews
      });
      this.template = _.template($('#expandable-tips-tpl').html());
    },

    render: function() {
      this.$el.html(this.template({ numHidden: this.numHidden() }));
      this.$('.tips-collection-placeholder').replaceWith(
        this.tipsCollectionView.render().$el);

      this.$('.tip-row').slice(this.numShown)
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
        this.$('.toggle-tips').html('&laquo; Hide tips');
      }
      this.expanded = !this.expanded;
    }
  });

  return {
    TipsCollectionView: TipsCollectionView,
    ExpandableTipsView: ExpandableTipsView
  };

});
