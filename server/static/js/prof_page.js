require(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ratings', 'util', 'review',
 'tips'],
function(backbone, $, _, ratings, util, _review, tips) {
  var averageRating = new ratings.RatingCollection(
    pageData.profRatings.filter(function(r) {
      return r.name !== 'overall';
    }));

  var averageRatingsView = new ratings.RatingsView({
    ratings: averageRating,
    subject: 'professor'
  });

  var kittenNum = util.getKittenNumFromName(pageData.profName);
  $('.prof-info-placeholder').replaceWith(
    _.template($('#prof-inner-tpl').html(), {
      'kittenNum': kittenNum
    })
  );

  $('.career-rating-placeholder').html(averageRatingsView.render().el);

  var numberOfCourses = pageData.profCourses.length;
  if (numberOfCourses > 1) {
    $('.number-of-courses').text(numberOfCourses + " Courses");
  } else if (numberOfCourses == 1) {
    $('.number-of-courses').text('1 Course');
  } else {
    $('.number-of-courses').text('No Courses Found');
  }

  var overallProfRating = _.find(pageData.profRatings, function(r) {
    return r.name === 'overall';
  });

  var ratingBoxView = new ratings.RatingBoxView({
    model: new ratings.RatingModel(overallProfRating)
  });

  $('#rating-box-container').html(ratingBoxView.render().el);

// For info on the jquery syntax used here, see:
// http://stackoverflow.com/questions/5598494/how-to-create-an-empty-non-null-
// jquery-object-ready-for-appending
  var tipsViews = $();
  _.each(window.pageData.tipObjsByCourse, function(courseReviews) {
    if (courseReviews.reviews.length === 0) {
      return;
    }
    var reviewCollection = new _review.ReviewCollection(courseReviews.reviews);
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
    var rendered_prof_review = $(tipsView.render().el);
    $('#tips-collection-container').replaceWith(rendered_prof_review.add(
        $('<div id=tips-collection-container></div')));
  });
  $(document.body).trigger('pageScriptComplete');
});
