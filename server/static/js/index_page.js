require(
['facebook', 'ext/jquery', 'util', 'sign_in', 'ext/cookie', 'ext/moment'],
function(_facebook, $, _util, _sign_in, _cookie, _moment) {
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

  var referrerId = _util.getReferrerId();
  if (referrerId) {
    mixpanel.track('Visit Referral Link', { referrerId: referrerId });
    $.cookie('referrer_id', referrerId, { expires: 30, path: '/' });
  } else {
    $.removeCookie('referrer_id');
  }

  _sign_in.renderEmailSignInModal();

  $('.email-link').click(function() {
    mixpanel.track('Sign in with email intent');
  });

  mixpanel.track('Impression: Landing page');

  $(document.body).trigger('pageScriptComplete');

  window.setTimeout(function() {
    $('#referral-contest').fadeIn(1000);
  }, 500);

  window.setInterval(function() {
    var duration = moment.duration(moment('2013-03-25 23:59:59 -0400').diff());
    $('#referral-contest')
      .find('.contest-hours').text(duration.hours()).end()
      .find('.contest-mins').text(duration.minutes()).end()
      .find('.contest-secs').text(duration.seconds()).end();
  }, 1000);
});
