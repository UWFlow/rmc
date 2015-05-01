define(
['ext/jquery', 'ext/underscore', 'ext/cookie', 'util'],
function($, _, __, _util) {

  var fbApiInit = false;
  var fbAppId;
  if (window.pageData.env === 'dev') {
    fbAppId = '289196947861602';
  } else if (window.pageData.env === 'test') {
    fbAppId = '194130524079471';
  } else {
    fbAppId = '219309734863464';
  }

  var _initializedFacebook = false;
  var initializedFacebook = function() {
    return _initializedFacebook;
  };

  var initFacebook = function(force) {
    if (force || !_initializedFacebook) {
      FB.init({appId: fbAppId, status: true, cookie: true, xfbml: true});
      _initializedFacebook = true;
    }
  };

  var fbSignedRequest;
  var fbid;
  window.fbAsyncInit = function() {
    initFacebook();
    FB.getLoginStatus(function(response) {
      if (response.status === 'connected') {
        fbSignedRequest = response.authResponse.signedRequest;
        fbid = response.authResponse.userID;
      }
      fbApiInit = true;
    });
  };

  // Load the SDK's source Asynchronously
  (function(d) {
    var js, id = 'facebook-jssdk', ref = d.getElementsByTagName('script')[0];
    if (d.getElementById(id)) {
      return;
    }
    js = d.createElement('script');
    js.id = id;
    js.async = true;
    js.src = '//connect.facebook.net/en_US/all.js';
    ref.parentNode.insertBefore(js, ref);
  }(document));

  var login = function(authResp, params, source, nextUrl) {
    params.fb_signed_request = authResp.signedRequest;
    var referrerId = $.cookie('referrer_id');
    params.referrer_id = referrerId;
    // TODO(Sandy): Logging to GA now assumes that the login will succeed, which
    // may not be the case. But if we make this request in the success handler,
    // it might not finish logging due to redirect. Though the login request
    // should normally succeed. Do this server side or on next page
    // TODO(Sandy): This logging call counts existing users who have already
    // "installed" Flow on Facebook. We should log each group individually?
    // TODO(Sandy): Assert source
    _gaq.push([
      '_trackEvent',
      'USER_GENERIC',
      'FACEBOOK_CONNECT_' + String(source).toUpperCase()
    ]);
    mixpanel.track('Facebook Connect', { source: source });
    if (referrerId) {
      // This is not a fully accurate calculation of sign ups via referral
      // link, but should be close.
      mixpanel.track('Facebook Connect Referral ', { referrerId: referrerId });
    }

    $.ajax('/login/facebook', {
      data: params,
      dataType: 'json',
      type: 'POST',
      success: function(data) {
        // Fail safe to make sure at least we sent off the _gaq trackEvent
        _gaq.push(function() {
          if (nextUrl) {
            window.location.href = '/profile?next=' +
              window.encodeURIComponent(nextUrl);
          } else {
            window.location.href = '/profile';
          }
        });
      },
      error: function(xhr) {
        window.location.href = '/';
      }
    });
  };


  // TODO(mack): this should be moved into its own backbone view
  var initConnectButton = function(attributes) {
    attributes = _.extend({
      source: 'UNKNOWN',
      nextUrl: undefined,
      // TODO(mack): make button element required parameter, rather than
      // assuming default class for button
      $button: $('.fb-login-button')
    }, attributes);

    // Facebook Connect button
    attributes.$button.click(function() {
      // TODO(Sandy): Put up drip loader here

      FB.login(function(response) {
        if (response.status !== 'connected') {
          // TODO(Sandy): Handle what happens when they don't login?
          return;
        }

        // Potentially first login, fetch user data from the FB Graph API
        var authResponse = response.authResponse;

        var deferredFriends = new $.Deferred();
        FB.api('/me/friends', function(response) {
          var fbids = _.pluck(response.data, 'id');
          deferredFriends.resolve(fbids);
        });

        var deferredMe = new $.Deferred();
        FB.api('/me', function(response) {
          deferredMe.resolve(response);
        });

        $.when(deferredMe, deferredFriends).done(function(me, friendFbids) {
          var params = {
            'friend_fbids': JSON.stringify(friendFbids),
            'first_name': me.first_name,
            'middle_name': me.middle_name,
            'last_name': me.last_name,
            'email': me.email,
            'gender': me.gender
          };
          login(authResponse, params, attributes.source, attributes.nextUrl);
        });
      }, {scope: 'public_profile,email,user_friends'});
    });
  };

  var logoPath = '/static/img/logo/flow_75x75.png';

  // Facebook will use the title, description, and images properties of the url
  var showSendDialogProfile = function(cb) {
    FB.ui({
      method: 'send',
      link: _util.getSiteBaseUrl() + '?meow=' + pageData.currentUserId.$oid
    }, cb);
  };

  /**
   * Options consist of:
   *    - link
   *    - name
   *    - caption
   *    - description
   *    - callback
   *    - picture (optional)
   */
  var showFeedDialog = function(options) {
    var picture = options.picture || _util.getSiteBaseUrl() + logoPath;
    FB.ui({
      method: 'feed',
      link: options.link,
      picture: picture,
      name: options.name,
      caption: options.caption,
      description: options.description
    }, options.callback);
  };

  // Ensure FB is fully initialized before calling any of its APIs. Solution
  // from http://stackoverflow.com/questions/3548493
  // TODO(mack): ensure that callbacks to fbEnsureInit() are queued/handled in
  // same order they come in
  function fbEnsureInit(cb) {
    if(!fbApiInit) {
      window.setTimeout(function() {
        fbEnsureInit(cb);
      }, 50);
    } else if(cb) {
      cb();
    }
  }

  var renewAccessToken = function() {
    if (fbSignedRequest) {
      $.ajax('/api/renew-fb', {
        data: { fb_signed_request: fbSignedRequest },
        dataType: 'json',
        type: 'POST',
        error: function(xhr) {
          // TODO(Sandy): Maybe code here to delay the next renew request? The
          // reason being that if facebook ever breaks down, then we'll
          // a warning logged to HipChat for every page-visit of a logged in
          // user...that's a lot.
        }
      });
    }
  };

  var checkAccessToken = function() {
    if (window.pageData.shouldRenewFbToken) {
      renewAccessToken();
    }
  };

  var subscribeEvents = function() {
    FB.Event.subscribe('edge.create',
      function(response) {
        mixpanel.track('Facebook Like', { fbid: fbid, url: response });
      }
    );

    FB.Event.subscribe('edge.remove',
      function(response) {
        mixpanel.track('Facebook Unlike', { fbid: fbid, url: response });
      }
    );
  };

  // These methods require that the FB api is fully initialized
  var ensureInitMethods = {
    initConnectButton: initConnectButton,
    showSendDialogProfile: showSendDialogProfile,
    checkAccessToken: checkAccessToken,
    showFeedDialog: showFeedDialog,
    subscribeEvents: subscribeEvents
  };
  // Ensure FB is initialized before calling any functions that require FB APIs
  _.each(ensureInitMethods, function(method, name) {
    ensureInitMethods[name] = function() {
      var args = arguments;
      fbEnsureInit(function() {
        method.apply(this, args);
      });
    };
  });

  $(ensureInitMethods.subscribeEvents);
  $(ensureInitMethods.checkAccessToken);

  return _.extend(ensureInitMethods, {
    initFacebook: initFacebook,
    initializedFacebook: initializedFacebook
  });
});
