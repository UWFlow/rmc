define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap', 'ext/slimScroll', 'course', 'facebook', 'work_queue'],
function(RmcBackbone, $, _, _s, bootstrap, __, _course, _facebook,
         _work_queue) {

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

      _.defer(_.bind(function() {
        this.$('.mutual-taking').tooltip({
          placement: 'in top'
        });
      }, this));

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
    },

    render: function() {
      _work_queue.add(function() {
        this.$el.empty();
        this.collection.each(function(model) {
          var view = this.createItemView(model, this.itemAttributes);
          view.tagName = 'section';
          // TODO(david): Append all at once for faster DOM rendering
          this.$el.append(view.render().el);
        }, this);

        this.postRender();
      }, this);

      return this;
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
        own_profile: pageData.ownProfile,
        invited_before: !!this.currentUser.get('num_invites'),
        // TODO(mack): get the points for first invite action from server
        first_invite_points: 100
      }));
      this.$('[rel="tooltip"]').tooltip();

      var collectionView = new FriendCollectionView({
        collection: this.friendCollection,
        itemAttributes: {
          currentUser: this.currentUser
        }
      });
      this.$('.friend-collection-placeholder').replaceWith(
        collectionView.render().$el);

      // Setup up FB Invite Friends buttons
      return this;
    },

    events: {
      'click .invite-friends-btn': 'onClickInviteFriendsBtn'
    },

    onClickInviteFriendsBtn: function(evt) {
      // Facebook engagement intent
      mixpanel.track('Facebook invite friends intent', {
        method: 'send',
        type: 'invite_friends',
        from_page: 'profile'
      });
      mixpanel.people.increment({'Facebook invite friends intent': 1});

      _facebook.showSendDialogProfile(
          _.bind(this.onSendDialogCallback, this));
    },

    onSendDialogCallback: function(response) {
      if (response && response.success) {
        // Facebook engagement completed
        mixpanel.track('Facebook invite friends completed', {
          method: 'send',
          type: 'invite_friends',
          from_page: 'profile'
        });
        mixpanel.people.increment({'Facebook invite friends completed': 1});
        this.onInviteSuccess();
      }
    },

    onInviteSuccess: function() {
      $.ajax('/api/invite_friend', {
        type: 'POST',
        dataType: 'json',
        success: _.bind(this.onInviteSuccessResponse, this)
      });
    },

    // TODO(mack): think of a better name
    onInviteSuccessResponse: function(resp) {
      this.currentUser.set({
        num_invites: resp.num_invites,
        num_points: this.currentUser.get('num_points') + resp.points_gained
      });

      // TODO(mack): maybe should call self.render() to update the star
      this.$('.invite-friends-btn .icon-star')
        .addClass('fill')
        .tooltip('destroy');
    }
  });


  return {
    FriendView: FriendView,
    FriendHovercardView: FriendHovercardView,
    FriendCollectionView: FriendCollectionView,
    FriendSidebarView: FriendSidebarView
  };
});
