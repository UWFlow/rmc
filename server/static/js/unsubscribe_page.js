require(
['ext/jquery'],
function($) {
  $('.unsubscribe_button').click(function() {
    mixpanel.track('Unsubscribe clicked', {
      unsubscriber_id: window.pageData.unsubscriber_id
    });

    // TODO(SANDY): DO SOMETHING HERE! PEOPLE MIGHT COME SOON
    //$.post('/api/user/unsubscribe',
  });

  mixpanel.track('Impression: Unsubscribe page');
});
