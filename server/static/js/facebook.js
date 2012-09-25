define(
['ext/jquery', 'ext/cookie', 'ext/facebook'],
function($, _cookie, FB) {

  if (window.pageData.env === 'dev') {
    var appId = '289196947861602';
  } else {
    var appId = '219309734863464';
  }

  FB.init({appId: appId, status: true, cookie: true, xfbml: true});

  var login = function(authResp, params) {
    // XXX(Sandy): Sending all this info in the cookie will easily allow
    // others to hijack someonne's session. We should probably look into
    // a way of verifying the request. Maybe that's what Facebook Signed
    // Requests are for?
    params.fb_signed_request = authResp.signedRequest;
    $.cookie('fbid', authResp.userID, { path: '/' });
    $.cookie('fb_access_token', authResp.accessToken, { path: '/' });
    $.cookie('fb_access_token_expires_in', authResp.expiresIn, { path: '/' });
    $.post(
      '/login',
      params,
      function(data) {
        // TODO(Sandy): handle errors here, expecting none right now though
        window.location.href = '/profile';
      }
    );
  };

  var firstLogin = function() {
    // TODO(Sandy): Put up drip loader here
    // First login, fetch user data from the FB Graph API
    // TODO(Sandy): Grab and send more data: name, email, faculty, program, uni
    // TODO(mack): could just get this from auth.login event, but this is
    // cleaner
    FB.getLoginStatus(function(response) {
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
  };

  var loginIfPossible = function() {
    FB.getLoginStatus(function(response) {
      // TODO(Sandy): Make redirect happen server-side so we don't even need to load the landing page
      // TODO(Sandy): Fetch user data here or better yet use realtime API to get friend updates
      if (response.status === 'connected') {
        // The user is already logged into Facebook and has ToSed our app before
        // Store the potentially updated access token in DB if necessary
        //var authResp = response.authResponse;
        login(response.authResponse, {});
      }
    });
  };

  return {
    firstLogin: firstLogin,
    loginIfPossible: loginIfPossible
  };

});
