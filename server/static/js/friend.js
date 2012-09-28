define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap', 'rmc_backbone', 'ext/slimScroll'],
function(Backbone, $, _, _s, bootstrap, RmcBackbone, __) {

  var FriendView = Backbone.View.extend({
    className: 'friend',

    initialize: function(options) {
      this.friendModel = options.friendModel;
    },

    render: function() {
      this.$el.html(
        _.template($('#friend-tpl').html(), this.friendModel.toJSON()));

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

      this.$('.mutual-courses')
        .popover({
          html: true,
          title: 'Mutual Courses',
          content: _.bind(this.getMutualCoursesPopoverContent, this),
          trigger: 'hover',
          placement: 'in right'
        })
        .click(function(evt) {
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
    },

    getMutualCoursesPopoverContent: function() {
      if (!this.mutualCoursesPopoverView) {
        this.mutualCoursesHovercardView = new MutualCoursesHovercardView({
          friendModel: this.friendModel
        });
      }
      var $el = this.mutualCoursesHovercardView.render().$el;
      window.setTimeout(function() {
        var maxHeight = 250;
        if ($el.find('.mini-courses').outerHeight() > maxHeight) {
          $el.slimScroll({
            height: maxHeight,
            width: $el.outerWidth(),
            alwaysVisible: true
          });
        }
      });
      return $el;
    }

  });


  var FriendHovercardView = Backbone.View.extend({
    className: 'friend-hovercard',

    initialize: function(options) {
      this.friendModel = options.friendModel;
    },

    render: function() {
      this.$el.html(
        _.template($('#friend-hovercard-tpl').html(),
          this.friendModel.toJSON()));

      return this;
    }
  });


  var MutualCoursesHovercardView = Backbone.View.extend({
    className: 'mutual-courses-hovercard',

    initialize: function(options) {
      this.friendModel = options.friendModel;
    },

    render: function() {
      this.$el.html(
        _.template($('#mutual-courses-hovercard-tpl').html(),
          this.friendModel.toJSON()));

      return this;
    }
  });


  var FriendCollectionView = RmcBackbone.CollectionView.extend({
    tagName: 'ol',
    className: 'friend-collection',

    createItemView: function(model) {
      return new FriendView({ friendModel: model });
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
        collection: this.friendCollection
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
  };
});
