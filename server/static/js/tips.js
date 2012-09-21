define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'ext/backbone', 'base_views', 'user', 'jquery.slide'],
function($, _, _s, bootstrap, Backbone, baseViews, user, jqSlide) {

  var Tip = Backbone.Model.extend({
    defaults: {
      userId: '1234',
      name: 'Mack Duan',
      comment: ''
    }
  });

  var TipView = Backbone.View.extend({
    render: function() {
      this.$el.html(_.template($('#tip-tpl').html(), this.model.toJSON()));
      return this;
    }
  });

  var TipsCollection = Backbone.Collection.extend({
    model: Tip
  });

  var TipsCollectionView = baseViews.CollectionView.extend({
    className: 'tips-collection',

    createItemView: function(model) {
      return new TipView({ model: model });
    }
  });

  // TODO(david): Make this fancier. Show more about tip person or something.
  var ExpandableTipsView = Backbone.View.extend({
    className: 'all-tips',
    expanded: false,
    numShown: 3,

    events: {
      'click .toggle-tips': 'toggleExpand'
    },

    initialize: function(options) {
      this.tips = options.tips;
      this.tipsCollectionView = new TipsCollectionView({
        collection: this.tips
      });
    },

    render: function() {
      this.$el.html(_.template($('#expandable-tips-tpl').html(), {
        numHidden: this.numHidden()
      }));
      this.$('.tips-collection-placeholder').replaceWith(
        this.tipsCollectionView.render().$el);

      this.$('.tip-row').slice(this.numShown)
        .wrapAll('<div class="expanded-tips hide-initial">');

      return this;
    },

    numTips: function() {
      return this.tips.length;
    },

    numHidden: function() {
      return this.numTips() - this.numShown;
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
    Tip: Tip,
    TipView: TipView,
    TipsCollection: TipsCollection,
    TipsCollectionView: TipsCollectionView,
    ExpandableTipsView: ExpandableTipsView
  };

});
