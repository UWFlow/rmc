define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap'],
function(Backbone, $, _, _s, __) {

  var FriendView = Backbone.View.extend({
    className: 'friend',

    initialize: function(options) {
      this.friendModel = options.friendModel;
    },

    render: function() {
      this.$el.html(
        _.template($('#friend-tpl').html(), this.friendModel.toJSON()))

      this.$('.friend-pic, .friend-name')
        .popover({
          html: true,
          title: this.friendModel.get('lastTermName'),
          content: _.bind(this.getFriendPopoverContent, this),
          trigger: 'hover',
          placement: 'in right'
        })
        .on('click', '.popover', function(evt) {
          // Prevent clicking in the hovercard from going to triggering the
          // link the hovercard is attached to
          return false;
        });

      return this;
    },

    getFriendPopoverContent: function() {
      if (!this.friendPopoverView) {
        this.friendHovercardView = new FriendHovercardView({
          friendModel: this.friendModel
        });
      }
      return this.friendHovercardView.render().$el;
    }

  });


  var FriendHovercardView = Backbone.View.extend({
    className: 'friend-hovercard',

    initialize: function(options) {
      this.friendModel = options.friendModel;
    },

    render: function() {
      this.$el.html(
        _.template($('#friend-hovercard-tpl').html(), this.friendModel.toJSON()));

      return this;
    }
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

    initialize: function(attributes) {
      this.friendCollection = attributes.friendCollection;
    },

    render: function() {
      this.$el.html(_.template($('#friend-sidebar-tpl').html(), {
        numFriends: this.friendCollection.length
      }));
      var collectionView = new FriendCollectionView({
        friendCollection: this.friendCollection
      });
      this.$('.friend-collection-placeholder').replaceWith(
        collectionView.render().$el);

      return this;
    }
  });


  return {
    FriendView: FriendView,
    FriendHovercardView: FriendHovercardView,
    FriendCollectionView: FriendCollectionView,
    FriendSidebarView: FriendSidebarView
  }
});
