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

  var ratingBoxView = new ratings.RatingBoxView({
    model: new ratings.RatingModel(courseModel.get('overall'))
  });
  $('#rating-box-container').html(ratingBoxView.render().el);

  var courseInnerView = new course.CourseInnerView({
    courseModel: courseModel
  });
  $('#course-inner-placeholder').html(courseInnerView.render().el);
  courseInnerView.animateBars();

  // TODO(mack): add prompt encouraging user to sign in to see friends
  // who've taken this course
  if (pageData.currentUserId) {
    var tookThisSidebarView = new tookThis.TookThisSidebarView({
      userCourses: courseModel.get('friend_user_courses'),
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
