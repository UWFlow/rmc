require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'transcript', 'util',
'fav_course', 'user_course', 'user'],
function($, _, _s, transcript, util, _fav_course, _user_course, _user) {

  if (window.pageData.currentUser) {
    _user.UserCollection.addToCache(window.pageData.currentUser);
  }

  // TODO(david): Maybe skip this step if user has a course in their favCourse?

  var userCourseModel = new _user_course.UserCourse(window.pageData.favCourse);
  var addFavCourseView = new _fav_course.AddFavCourseView({
    favCourse: userCourseModel
  });

  // FIXME(david): Don't show if someone already has a fav course selected
  $('#add-fav-course-placeholder').replaceWith(addFavCourseView.render().el);

});
