require(
['ext/jquery'],
function($) {
  $('.unsubscribe_button').click(function() {
    mixpanel.track('Unsubscribe clicked', {
      unsubscribe_user: window.pageData.unsubscribe_user
    });

    $.post(
      '/api/user/unsubscribe', {
        pasta: window.pageData.unsubscribe_user
      }).complete(function() {
        // Failing should have sent a warning to HipChat
        window.location.href = '/';
      });
  });

  mixpanel.track('Impression: Unsubscribe page');

  $(document.body).trigger('pageScriptComplete');
});
