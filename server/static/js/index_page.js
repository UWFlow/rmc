define(
['facebook', 'ext/jquery', 'util', 'sign_in'],
function(_facebook, $, _util, _sign_in) {
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

  _sign_in.renderEmailSignInModal();

  $('.email-link').click(function() {
    mixpanel.track('Sign in with email intent');
  });

  mixpanel.track('Impression: Landing page');
});
