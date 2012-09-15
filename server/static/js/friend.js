define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string'],
function(Backbone, $, _, _s) {

  var FriendModel = Backbone.Model.extend({
    defaults: {
      id: 1647810326,
      name: 'Mack Duan',
      lastTermName: 'Fall 2012',
      coursesTook: []
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

    events: {
      'mouseenter .friend-pic': 'showHovercard',
      'mouseleave .friend-pic': 'hideHovercard',
      'mouseenter .friend-name': 'showHovercard',
      'mouseleave .friend-name': 'hideHovercard'
    },

    showHovercard: function(evt) {
      var $target = $(evt.currentTarget);
      this.hovercardView = new FriendHovercardView({
        friendModel: this.friendModel
      });
      var $hovercard = this.hovercardView.render().$el;
      $target.append($hovercard);
      $hovercard.css({
        left: $target.outerWidth() + 10 - window.parseInt($hovercard.css('padding-left'), 10),
        // TODO(mack): remove hardcode of -30 which must be kept in sync with
        // arrow offset in css; might require adding div for arrow to html to
        // remove hardcode since cannot access css of pseudoclass from jQuery
        top: $target.outerHeight()/2 - 30 - window.parseInt($hovercard.css('padding-top'), 10)
      });
    },

    hideHovercard: function(evt) {
      this.hovercardView.remove();
      this.hovercardView.unbind();
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
        numFriends: this.friendCollection.length
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
    FriendHovercardView: FriendHovercardView,
    FriendCollection: FriendCollection,
    FriendCollectionView: FriendCollectionView,
    FriendSidebarView: FriendSidebarView
  }
});
