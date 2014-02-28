require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'rmc_moment', 'util'],
function($, _, _s, moment, _util) {

  var POLLING_DELAY = 3 * 60 * 1000;
  // Stop refreshing after an hour, incase we leave tabs open :(
  var CUTOFF_COUNT = 60;
  var timesRefreshed = 0;
  var reviewTemplate =  _.template($('#review-info-tpl').html());

  var pollStats = function() {
    $.post(
      '/admin/api/generic-stats',
      {},
      function(resp) {
        // TODO(Sandy) : User actions (ratings/reviews) in the past day/hour etc
        // Last x users signed up
        // last x reivews/ratings
        $('#num_users').text(resp.num_users);
        $('#num_signups_today').text(resp.num_signups_today);
        $('#users_with_transcript_ratio').text(_s.sprintf('%.2f (%d / %d)',
            resp.num_users_with_transcript / resp.num_users,
            resp.num_users_with_transcript,
            resp.num_users));
        $('#users_with_schedule_ratio').text(_s.sprintf('%.2f (%d / %d)',
          resp.num_users_with_schedule / resp.num_users,
          resp.num_users_with_schedule,
          resp.num_users));
        $('#num_ratings').text(resp.num_ratings);
        $('#num_reviews').text(resp.num_reviews);
        $('#ucs_rated_reviewed_ratio').text(_s.sprintf('%.2f (%d / %d)',
            resp.num_ucs_rated_reviewed / resp.num_ucs,
            resp.num_ucs_rated_reviewed,
            resp.num_ucs));
        $('#courses_rated_reviewed_ratio').text(_s.sprintf('%.2f (%d / %d)',
            resp.num_courses_rated_reviewed / resp.num_courses,
            resp.num_courses_rated_reviewed,
            resp.num_courses));
        $('#users_rated_reviewed_ratio').text(_s.sprintf('%.2f (%d / %d)',
            resp.num_users_rated_reviewed / resp.num_users,
            resp.num_users_rated_reviewed,
            resp.num_users));
        setReviews(resp.latest_reviews);
        setLastUpdatedTime(_util.toDate(resp.epoch));
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

  var setReviews = function(reviews) {
    $('.reviews').html("");
    _.each(reviews, function(review) {
      $('.reviews').append(reviewTemplate({'review': review}));
    });
  };

  var init = function() {
    setLastUpdatedTime(window.pageData.epoch.$date);
    setReviews(window.pageData.latest_reviews);
    pollStats();
  };

  $(init);
});
