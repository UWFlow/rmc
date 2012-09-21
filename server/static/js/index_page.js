require(
['ext/jquery', 'ext/cookie', 'ext/facebook'],
function($, _cookie, FB) {
  if (window.pageData.env === 'dev') {
    var appId = '289196947861602';
  } else {
    var appId = '219309734863464';
  }

  FB.init({appId: appId, status: true, cookie: true, xfbml: true});

  FB.Event.subscribe('auth.login', function(response) {
    if (response.status === 'connected') {
      // TODO(Sandy): Put up drip loader here
      // First login, fetch user data from the FB Graph API
      // TODO(Sandy): Grab and send more data: name, email, faculty, program, uni
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
        var authResp = response.authResponse;
        $.cookie('fbid', authResp.userID, { path: '/' });
        $.cookie('fb_access_token', authResp.accessToken, { path: '/' });
        $.cookie('fb_access_token_expires_in', authResp.expiresIn, { path: '/' });
        $.post(
          '/login',
          {
            'friend_fbids': JSON.stringify(friendFbids),
            'first_name': me.first_name,
            'middle_name': me.middle_name,
            'last_name': me.last_name,
            'email': me.email,
            'gender': me.gender
          },
          function(data) {
          // TODO(Sandy): handle errors here, expecting none right now though
          window.location.href = '/profile';
        });
      });
    }
  });

  FB.getLoginStatus(function(response) {
    // TODO(Sandy): Make redirect happen server-side so we don't even need to load the landing page
    // TODO(Sandy): Fetch user data here or better yet use realtime API to get friend updates
    if (response.status === 'connected') {
      window.location.href = '/profile';
    }
  });

});
