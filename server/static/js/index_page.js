require(
['facebook', 'ext/jquery', 'util'],
function(_facebook, $, util) {
  if (util.getQueryParam('logout')) {
    _facebook.logout();
  } else {
    _facebook.loginIfPossible();
  }

  // Facebook connect button A/B test
  if (util.getQueryParam('ft')) {
    $('.fb-login-text').text('See what friends are taking');
  }

  $('.header-bg').css('opacity', 1.0);
  $('.sign-up-box').addClass('animated');

  window.setTimeout(function() {
    _facebook.initConnectButton();
  }, 3000);
});
