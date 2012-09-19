require(
['ext/jquery', 'ext/cookie'],
function($, _cookie) {
  $(function() {
    window.fbAsyncInit = function() {
      FB.init({appId: '219309734863464', status: true, cookie: true, xfbml: true});

      FB.Event.subscribe('auth.login', function(response) {
        if (response.status === 'connected') {
          // TODO(Sandy): Put up drip loader here
          // First login, fetch user data from the FB Graph API
          // TODO(Sandy): Grab and send more data: name, email, faculty, program, uni
          FB.api('/me/friends', function(response) {
            var fbids = [];
            for (var ii in response.data) {
              fbids.push(response.data[ii].id);
            }
            var friends = JSON.stringify(fbids);
            $.post('/login', { 'friends': friends }, function(data) {
              // TODO(Sandy): handle errors here, expecting none right now though
              window.location.href = '/profile'
            });
          });

          authResp = response.authResponse;
          $.cookie('fbid', authResp.userID, { path: '/' });
          $.cookie('fb_access_token', authResp.accessToken, { path: '/' });
          $.cookie('fb_access_token_expires_in', authResp.expiresIn, { path: '/' });
        }
      });

      FB.getLoginStatus(function(response) {
        // TODO(Sandy): Make redirect happen server-side so we don't even need to load the landing page
        // TODO(Sandy): Fetch user data here or better yet use realtime API to get friend updates
        if (response.status === 'connected') {
          window.location.href = '/profile'
        }
      });
    };
    (function() {
      var e = document.createElement('script');
      e.type = 'text/javascript';
      e.src = document.location.protocol +
          '//connect.facebook.net/en_US/all.js';
      e.async = true;
      document.getElementById('fb-root').appendChild(e);
    })();
  });
});
