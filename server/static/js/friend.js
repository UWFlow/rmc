define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string'],
function(Backbone, $, _, _s) {

  var FriendModel = Backbone.Model.extend({
    defaults: {
      'id': 1647810326,
      'name': 'Mack Duan',
      'courses_took': ['CS137', 'SE145', 'ECE222']
    }
  });

  var FriendView = Backbone.View.extend({
    className: 'friend',

    initialize: function(options) {
      this.friendModel = options.friendModel;
    },

    render: function() {
      this.$el.html(
        _.template($('#friend-tpl').html(), this.friendModel.toJSON()))

      return this;
    },
  });


  var FriendCollection = Backbone.Collection.extend({
    model: FriendModel,
  });


  // TODO(mack): make generic CollectionView
  var FriendCollectionView = Backbone.View.extend({
    tagName: 'ol',
    className: 'friend-collection',

    initialize: function(options) {
      this.friendCollection = options.friendCollection;
      this.friendViews = [];
    },

    render: function() {
      this.$el.empty();
      this.friendCollection.each(function(friendModel) {
        var friendView = new FriendView({
          friendModel: friendModel,
          tagName: 'li'
        });
        this.$el.append(friendView.render().el);
        this.friendViews.push(friendView);
      }, this);

      return this;
    }
  });

  FriendSidebarView = Backbone.View.extend({
    className: 'friend-sidebar',

    initialize: function(options) {
      this.friendCollection = options.friendCollection;
    },

    render: function() {
      this.$el.html(_.template($('#friend-sidebar-tpl').html(), {
        num_friends: this.friendCollection.length
      }));
      var collectionView = new FriendCollectionView({
        friendCollection: this.friendCollection
      });
      this.$('.friend-collection-placeholder').replaceWith(
        collectionView.render().el);

      return this;
    }
  });

  return {
    FriendModel: FriendModel,
    FriendView: FriendView,
    FriendCollection: FriendCollection,
    FriendCollectionView: FriendCollectionView,
    FriendSidebarView: FriendSidebarView
  }
});
