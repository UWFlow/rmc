define(
['facebook', 'ext/jquery', 'util'],
function(_facebook, $, _util) {
  $('.header-bg').css('opacity', 1.0);
  $('.sign-up-box').addClass('animated');

  var next = _util.getQueryParam('next');
  var nextUrl;
  if (next) {
    nextUrl = '/profile?next=' + next;
  }
  _facebook.initConnectButton({
    source: 'HOME',
    nextUrl: nextUrl
  });

  mixpanel.track('Impression: Landing page');
});
