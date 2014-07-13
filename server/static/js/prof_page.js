require(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ratings', 'util', 'review',
 'tips'],
function(backbone, $, _, ratings, util, review, tips) {

  var overallRatings = _.filter(pageData.profRatings, function(r) {
    return r.name !== 'overall';
  });
  var averageRating = new ratings.RatingCollection(overallRatings);

  var averageRatingsView = new ratings.RatingsView({
    ratings: averageRating,
    subject: 'professor'
  });

  var kittenNum = util.getKittenNumFromName(pageData.profName);
  var profInner =  _.template($('#prof-inner-tpl').html(), {
    'kittenNum': kittenNum
  })
  $('.prof-info-placeholder').replaceWith(profInner);

  $('.career-rating-placeholder').html(averageRatingsView.render().el);

  var overallProfRating = _.find(pageData.profRatings, function(r) {
    return r.name === 'overall';
  });

  var ratingBoxView = new ratings.RatingBoxView({
    model: new ratings.RatingModel(overallProfRating)
  });

  $('#rating-box-container').html(ratingBoxView.render().el);

  _.each(window.pageData.tipObjsByCourse, function(courseReviews) {
    if (courseReviews.reviews.length === 0) {
      return;
    }
    var reviewCollection = new review.ReviewCollection(courseReviews.reviews);
    var fullCourse = _.find(window.pageData.profCoursesFull,
        function(course) {
          return course.id === courseReviews.course_id;
        }
    );
    var tipsView = new tips.ExpandableTipsView({
      reviews: reviewCollection,
      numShown: 3,
      course: fullCourse,
      pageType: 'prof'
    });
    var renderedProfReviews = $(tipsView.render().el);
    $('#tips-collection-container').replaceWith(renderedProfReviews.add(
        $('<div id=tips-collection-container></div')));
  });
  $(document.body).trigger('pageScriptComplete');
});
