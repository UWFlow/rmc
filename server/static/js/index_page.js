require(
['facebook', 'ext/jquery', 'util'],
function(_facebook, $, util) {
  $('.header-bg').css('opacity', 1.0);
  $('.sign-up-box').addClass('animated');

  _facebook.initConnectButton('HOME');

  mixpanel.track('Impression: Landing page');
});
