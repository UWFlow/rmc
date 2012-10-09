require(
['facebook', 'ext/jquery', 'util'],
function(facebook, $, util) {
  if (util.getQueryParam('logout')) {
    facebook.logout();
  } else {
    facebook.loginIfPossible();
  }

  $('.header-bg').css('opacity', 1.0);
  $('.sign-up-box').addClass('animated');
});
