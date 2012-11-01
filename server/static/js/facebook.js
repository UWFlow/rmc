define(
['ext/jquery', 'ext/underscore', 'ext/cookie'],
function($, _, __) {

  var fbApiInit = false;
  if (window.pageData.env === 'dev') {
    var fbAppId = '289196947861602';
  } else {
    var fbAppId = '219309734863464';
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

  window.fbAsyncInit = function() {
    initFacebook();
    FB.getLoginStatus(function(response) {
      fbApiInit = true;
    });
  };

  // Load the SDK's source Asynchronously
  (function(d){
    var js, id = 'facebook-jssdk', ref = d.getElementsByTagName('script')[0];
    if (d.getElementById(id)) {return;}
    js = d.createElement('script'); js.id = id; js.async = true;
    js.src = '//connect.facebook.net/en_US/all.js';
    ref.parentNode.insertBefore(js, ref);
  }(document));

  var login = function(authResp, params, source, nextUrl) {
    // FIXME[uw](Sandy): Sending all this info in the cookie will easily allow
    // others to hijack someonne's session. We should probably look into
    // a way of verifying the request. Maybe that's what Facebook Signed
    // Requests are for? There are two corresponding server-side FIXMEs for this
    params.fb_signed_request = authResp.signedRequest;
    // TODO(Sandy): When switching over to Flask sessions be sure to remove
    // these old cookies
    $.cookie('fbid', authResp.userID, { expires: 365, path: '/' });
    $.cookie('fb_access_token', authResp.accessToken,
        { expires: 365, path: '/' });
    $.cookie('fb_access_token_expires_in', authResp.expiresIn,
        { expires: 365, path: '/' });
    // TODO(Sandy): This assumes the /login request will succeed, which may not
    // be the case. But if we make this request in the success handler, it might
    // not get logged at all (due to redirect). We could setTimeout it, but that
    // would cause delay and also I think /login should normally just be
    // successful. Do this server side or on next page
    // TODO(Sandy): This counts people whose cookies were dead, but have
    // already TOSed Flow on Facebook. We should log each group individually
    // TODO(Sandy): Assert source
    _gaq.push([
      '_trackEvent',
      'USER_GENERIC',
      'FACEBOOK_CONNECT_' + String(source).toUpperCase()
    ]);
    mixpanel.track('Facebook Connect', { source: source });

    $.ajax('/login', {
      data: params,
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
        FB.logout(function() {
          window.location.href = '/';
        });
      }
    });
  };


  // TODO(mack): this should be moved into its own backbone view
  var initConnectButton = function(attributes) {
    attributes = _.extend({
      source: 'UNKNOWN',
      nextUrl: undefined
    }, attributes);

    // Facebook Connect button
    $('.fb-login-button').click(function() {
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
      }, {scope: 'email'});
    });
  };

  var showSendDialogProfile = function(cb) {
    // TODO(Sandy): Don't hardcode link?
    var sendDialogLink = 'http://uwflow.com';

    FB.ui({
        method: 'send',
        name: 'Flow',
        link: sendDialogLink,
        picture: sendDialogLink + '/static/img/logo/flow_75x75.png',
        description: 'Plan your courses with friends in mind!'
      }, cb);
  };

  // Ensure FB is fully initialized before calling any of its APIs. Solution
  // from http://stackoverflow.com/questions/3548493/how-to-detect-when-facebooks-fb-init-is-complete
  // TODO(mack): ensure that callbacks to fbEnsureInit() are queued/handled in same
  // order they come in
  function fbEnsureInit(cb) {
    if(!fbApiInit) {
      window.setTimeout(function() {
        fbEnsureInit(cb);
      }, 50);
    } else if(cb) {
      cb();
    }
  }

  // These methods require that the FB api is fully initialized
  var ensureInitMethods = {
    initConnectButton: initConnectButton,
    showSendDialogProfile: showSendDialogProfile
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

  return _.extend(ensureInitMethods, {
    initFacebook: initFacebook,
    initializedFacebook: initializedFacebook
  });
});
