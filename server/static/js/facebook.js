define(
['ext/jquery', 'ext/cookie', 'ext/facebook'],
function($, __, FB) {

  if (window.pageData.env === 'dev') {
    var appId = '289196947861602';
  } else {
    var appId = '219309734863464';
  }

  FB.init({appId: appId, status: true, cookie: true, xfbml: true});

  // Facebook Connect button
  $('.fb-login-button').click(function() {
    // TODO(Sandy): Put up drip loader here
    FB.login(function(response) {
      if (response.status !== 'connected') {
        // TODO(Sandy): Handle what happens when they don't login?
        return;
      }

      // First login, fetch user data from the FB Graph API
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
        login(authResponse, params);
      });
    });
  });

  var login = function(authResp, params) {
    // FIXME[uw](Sandy): Sending all this info in the cookie will easily allow
    // others to hijack someonne's session. We should probably look into
    // a way of verifying the request. Maybe that's what Facebook Signed
    // Requests are for? There are two corresponding server-side FIXMEs for this
    params.fb_signed_request = authResp.signedRequest;
    $.cookie('fbid', authResp.userID, { path: '/' });
    $.cookie('fb_access_token', authResp.accessToken, { path: '/' });
    $.cookie('fb_access_token_expires_in', authResp.expiresIn, { path: '/' });
    $.ajax('/login', {
      data: params,
      type: 'POST',
      success: function(data) {
        // TODO(Sandy): handle errors here, expecting none right now though
        window.location.href = '/profile';
      },
      error: function(xhr) {
        FB.logout(function() {
          window.location.href = '/';
        });
      }
    });
  };

  // TODO(Sandy): MARKED FOR DELETEION. Now that we redirect from the server, we
  // might not need this logic here. We should consider if there are any other
  // cases that needs this logic (eg. maybe we want the user to be able to see
  // the landing page?)
  var loginIfPossible = function() {
    FB.getLoginStatus(function(response) {
      // TODO(Sandy): Make redirect happen server-side so we don't even need to load the landing page
      // TODO(Sandy): Fetch user data here or better yet use realtime API to get friend updates
      if (response.status === 'connected') {
        // The user is already logged into Facebook and has ToSed our app before
        // Store the potentially updated access token in DB if necessary
        login(response.authResponse, {});
      }
    });
  };

  var logout = function(cb) {
    $.removeCookie('fbid');
    $.removeCookie('fb_access_token');
    $.removeCookie('fb_access_token_expires_in');
    FB.logout(cb);
  };

  return {
    loginIfPossible: loginIfPossible,
    logout: logout
  };

});
