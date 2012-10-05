require(
['ext/jquery','course', 'took_this', 'user', 'tips', 'prof', 'ratings',
'user_course'],
function($, course, tookThis, user, tips, prof, ratings, user_course) {

  course.CourseCollection.addToCache(pageData.courseObj);
  user.UserCollection.addToCache(pageData.userObjs);
  user_course.UserCourses.addToCache(pageData.userCourseObjs);

  var courseObj = pageData.courseObj;
  var courseModel = course.CourseCollection.getFromCache(courseObj.id);
  var userCourse = courseModel.get('user_course');

  var overallRating = courseModel.getOverallRating();
  var ratingBoxView = new ratings.RatingBoxView({ model: overallRating });
  $('#rating-box-container').html(ratingBoxView.render().el);

  var courseInnerView = new course.CourseInnerView({
    courseModel: courseModel,
    userCourse: userCourse
  });
  $('#course-inner-placeholder').html(courseInnerView.render().el);
  courseInnerView.animateBars();

  // TODO(mack): add prompt encouraging user to sign in to see friends
  // who've taken this course
  if (pageData.currentUserId) {
    // Sort friends who've taken this by term
    sorted_friend_user_courses = courseModel.get('friend_user_courses');
    sorted_friend_user_courses.comparator = function(uc1, uc2) {
      var retVal;
      if (uc1.get('term_id') > uc2.get('term_id')) {
        retVal = -1;
      } else if (uc1.get('term_id') < uc2.get('term_id')) {
        retVal = 1;
      } else {
        retVal = 0;
      }
      return retVal;
    };
    sorted_friend_user_courses.sort();

    var tookThisSidebarView = new tookThis.TookThisSidebarView({
      userCourses: sorted_friend_user_courses,
      courseCode: courseModel.get('code')
    });
    $('#took-this-sidebar-container').html(tookThisSidebarView.render().el);
  }

  // TODO(Sandy): Use the comment_date field
  var tipObjs = window.pageData.tipObjs;
  var tipsCollection = new tips.TipsCollection(tipObjs);

  var tipsView = new tips.ExpandableTipsView({ tips: tipsCollection });
  $('#tips-collection-placeholder').replaceWith(tipsView.render().el);

  // TODO(david): Handle no professors for course
  var profsCollection = new prof.ProfCollection(courseModel.get('professors'));
  var profsView = new prof.ProfCollectionView({ collection: profsCollection });
  $('#professor-review-container').html(profsView.render().el);

});
