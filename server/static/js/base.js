// TODO(david): This should be in main.js, but is here as a temporary workaround
//     because main.js?version doesn't get updated on deploy. (Sorry, its 7 am
//     and I have to get up for SE Open House tomorrow so I don't have time to
//     figure out Require.js.)

define(['ext/jquery', 'ext/underscore', 'ext/bootstrap'],
function($, _, _bootstrap) {

  $('.navbar .signout-btn').tooltip({
    title: 'Sign out',
    placement: 'bottom'
  }).click(function() {
    $.removeCookie('fbid', { path: '/' });
    $.removeCookie('fb_access_token', { path: '/' });
    $.removeCookie('fb_access_token_expires_in', { path: '/' });
    window.location.href = '/?logout=1';
  });

  // Async-load footer background image
  var $footer = $('footer');
  if ($footer.length && window.location.pathname !== '/') {
    window.setTimeout(function() {
      $footer.css('background',
          'url(/static/img/footer_uw_sphere.jpg) left top no-repeat');
    }, 100);
  }

});
