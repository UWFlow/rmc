define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap', 'ext/slimScroll', 'course', 'facebook'],
function(RmcBackbone, $, _, _s, bootstrap, __, _course, _facebook) {

  var FriendView = RmcBackbone.View.extend({
    className: 'friend',

    initialize: function(attributes) {
      this.friendModel = attributes.friendModel;
      this.isFriendClickable = attributes.isFriendClickable;
      this.mutualCourses = this.friendModel.get('mutual_courses');
    },

    render: function() {
      this.$el.html(
        _.template($('#friend-tpl').html(), {
          friend: this.friendModel,
          is_friend_clickable: this.isFriendClickable,
          mutual_courses: this.mutualCourses,
          own_profile: pageData.ownProfile
        }));

      if (!pageData.ownProfile) {
        return this;
      }

      var lastTermCourses = this.friendModel.get('last_term_courses');
      if (lastTermCourses.length) {
        this.$('.friend-name')
          .popover({
            html: true,
            title: this.friendModel.get('last_term_name'),
            content: _.bind(this.getFriendPopoverContent, this),
            trigger: 'hover',
            placement: 'in right'
          })
          .on('click', '.popover', function(evt) {
            // Prevent clicking in the hovercard from going to triggering the
            // link the hovercard is attached to
            if (!$(evt.target).is('a')) {
              return false;
            }
          });
      }

      var mutualCourses = this.friendModel.get('mutual_courses');
      if (mutualCourses.length) {
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
            if (!$(evt.target).is('a')) {
              return false;
            }
          });
      }

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
          friendModel: this.friendModel,
          mutualCourses: this.mutualCourses
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


  var FriendHovercardView = RmcBackbone.View.extend({
    className: 'friend-hovercard',

    initialize: function(attributes) {
      this.friendModel = attributes.friendModel;
    },

    render: function() {
      this.$el.html(
        _.template($('#friend-hovercard-tpl').html(), {
          friend: this.friendModel.toJSON(),
          last_term_courses: this.friendModel.get('last_term_courses'),
          last_term_name: this.friendModel.get('last_term_name')
        }
      ));

      _.defer(function() {
        this.$('.mutual-taking').tooltip({
          placement: 'in top'
        });
      });

      return this;
    }
  });


  var MutualCoursesHovercardView = RmcBackbone.View.extend({
    className: 'mutual-courses-hovercard',

    initialize: function(options) {
      this.friendModel = options.friendModel;
      this.mutualCourses = options.mutualCourses;
    },

    render: function() {
      this.$el.html(
        _.template($('#mutual-courses-hovercard-tpl').html(), {
          friend: this.friendModel,
          mutual_courses: this.mutualCourses
        }));

      return this;
    }
  });


  var FriendCollectionView = RmcBackbone.CollectionView.extend({
    tagName: 'ol',
    className: 'friend-collection',

    createItemView: function(model, itemAttributes) {
      // Only friends of currentUser (and currentUser) should be clickable
      var currentUser = itemAttributes.currentUser;
      var isFriendClickable = false;
      if (currentUser) {
        var clickableIds = currentUser.get('friend_ids');
        clickableIds.push(currentUser.get('id'));
        // TODO(Sandy): Optimize if slow for many friends?
        if (_.contains(currentUser.get('friend_ids'), model.get('id'))) {
          isFriendClickable = true;
        }
      }

      return new FriendView({
        friendModel: model,
        isFriendClickable: isFriendClickable
      });
    }
  });

  var FriendSidebarView = RmcBackbone.View.extend({
    className: 'friend-sidebar',

    initialize: function(attributes) {
      this.currentUser = attributes.currentUser;
      this.friendCollection = attributes.friendCollection;
    },

    render: function() {
      this.$el.html(_.template($('#friend-sidebar-tpl').html(), {
        num_friends: this.friendCollection.length,
        own_profile: pageData.ownProfile
      }));
      var collectionView = new FriendCollectionView({
        collection: this.friendCollection,
        itemAttributes: {
          currentUser: this.currentUser
        }
      });
      this.$('.friend-collection-placeholder').replaceWith(
        collectionView.render().$el);

      // Setup up FB Invite Friends buttons
      this.$('.invite-friends-btn').click(function() {
        // Facebook engagement intent
        mixpanel.track('Facebook invite friends intent', {
          method: 'send',
          type: 'invite_friends',
          from_page: 'profile'
        });
        mixpanel.people.increment({'Facebook invite friends intent': 1});

        _facebook.showSendDialogProfile(function(response) {
          if (response && response.success) {
            // Facebook engagement completed
            mixpanel.track('Facebook invite friends completed', {
              method: 'send',
              type: 'invite_friends',
              from_page: 'profile'
            });
            mixpanel.people.increment({'Facebook invite friends completed': 1});
          }
        });
      });
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
