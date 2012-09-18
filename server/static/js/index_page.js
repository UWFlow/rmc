require(
['ext/jquery'],
function($) {
  $(function() {
    window.fbAsyncInit = function() {
      FB.init({appId: '219309734863464', status: true, cookie: true, xfbml: true});

      FB.Event.subscribe('auth.login', function(response) {
        if (response.status === 'connected') {
          window.location.href = '/profile'
        }
      });

      FB.getLoginStatus(function(response) {
        // TODO(Sandy): Make redirect happen server-side so we don't even need to
        // load the landing page
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
