define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap', 'rmc_backbone'],
function(Backbone, $, _, _s, bootstrap, RmcBackbone) {

  // TODO(david): Sorry about the terrible name of everything... I'm tired

  var TookThisView = Backbone.View.extend({
    className: 'took-this',

    render: function() {
      this.$el.html(_.template($('#took-this-tpl').html(),
          this.model.toJSON()));
      return this;
    }
  });

  var UserCollectionView = RmcBackbone.CollectionView.extend({
    className: 'took-this-collection',

    createItemView: function(model) {
      return new TookThisView({ model: model });
    }
  });

  TookThisSidebarView = Backbone.View.extend({
    className: 'took-this-sidebar',

    initialize: function(attributes) {
      this.courseCode = attributes.courseCode;
      this.collection = attributes.collection;
    },

    render: function() {
      this.$el.html(_.template($('#took-this-sidebar-tpl').html(), {
        numFriends: this.collection.length,
        courseCode: this.courseCode
      }));
      var collectionView = new UserCollectionView({
        collection: this.collection
      });
      this.$('.took-this-collection-placeholder').replaceWith(
        collectionView.render().$el);

      return this;
    }
  });

  return {
    TookThisView: TookThisView,
    TookThisSidebarView: TookThisSidebarView
  };
});
