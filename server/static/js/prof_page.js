require(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ratings', 'util', 'review',
 'tips', 'sign_in'],
function(backbone, $, _, ratings, util, _review, tips, _sign_in) {
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

  var overallProfRating = _.find(pageData.profRatings, function(r) {
    return r.name === 'overall';
  });

  var ratingBoxView = new ratings.RatingBoxView({
    model: new ratings.RatingModel(overallProfRating)
  });

  $('#rating-box-container').html(ratingBoxView.render().el);

  $('.prof-courses-placeholder').replaceWith(
      _.template($('#prof-courses-tpl').html(), {
          'courses': window.pageData.profCourses
      })
  );

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
    //tipsViews = tipsViews.add(tipsView.render().el);
  });
  //$('#tips-collection-container').replaceWith(
    //      $('<empty-root>').append(tipsViews).html());
  $(document.body).trigger('pageScriptComplete');
});
