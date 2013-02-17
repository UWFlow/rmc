require(
['ext/jquery', 'util'],
function($, _util) {
  var POLLING_DELAY = 60000;
  // Stop refreshing after an hour, incase we leave tabs open :(
  var CUTOFF_COUNT = 60;

  var timesRefreshed = 0;

  var reviewDiv = function(review) {
    var user_id = review.user_id.$oid;
    var course_id = review.course_id.toUpperCase();
    var professor_id = review.professor_id.$oid;
    var text = review.text;
    var type = review.type;
    return '<div class="review">' +
      //'<div class="review-user-id">' + user_id + '</div>' +
      '<div class="review-course-id">' + course_id + '</div>' +
      //'<div class="review-professor-id">' + professor_id + '</div>' +
      '<div class="review-text">' + text + '</div>' +
      '<div class="review-type">' + type + '</div>' +
    '</div>';
  };

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
        $('#num_users_with_transcript').text(resp.num_users_with_transcript);
        $('#num_ucs').text(resp.num_ucs);
        $('#num_ratings').text(resp.num_ratings);
        $('#num_reviews').text(resp.num_reviews);
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
      $('.reviews').append(reviewDiv(review));
    });
  };

  var init = function() {
    setLastUpdatedTime(window.pageData.epoch.$date);
    setReviews(window.pageData.latest_reviews);
    setTimeout(pollStats, POLLING_DELAY);
  };

  $(init);
});
