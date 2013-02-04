require(
['ext/jquery'],
function($) {
  var POLLING_DELAY = 60000;
  // Stop refreshing after an hour, incase we leave tabs open :(
  var CUTOFF_COUNT = 60;

  var timesRefreshed = 0;
  var pollStats = function() {
    console.log('this is actually hapnnieng');
    $.post(
      '/admin/api/generic-stats',
      {},
      function(resp) {
        // TODO(Sandy) : User actions (ratings/reviews) in the past day/hour etc
        // Last x users signed up
        // last x reivews/ratings
        $('#num_users').text(resp.num_users);
        $('#num_signups_today').text(resp.num_signups_today);
        $('#num_users_with_transcript').text(resp.num_users_with_transcript);
        $('#num_ucs').text(resp.num_ucs);
        setLastUpdatedTime(resp.epoch.$date);
      },
      'json'
    );
    timesRefreshed += 1;
    if (timesRefreshed < CUTOFF_COUNT) {
      setTimeout(pollStats, POLLING_DELAY);
    }
  };

  var setLastUpdatedTime = function(time) {
    $('#last_updated').text(moment(time).toString());
  };

  var init = function() {
    setLastUpdatedTime(window.pageData.epoch.$date);
    setTimeout(pollStats, POLLING_DELAY);
  };

  $(init);
});
