require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'transcript', 'util',
'fav_course', 'user_course'],
function($, _, _s, transcript, util, _fav_course, _user_course) {

  // FIXME(david): We should get this from the server in case the user already
  //     has a favourite course
  var userCourse = new _user_course.UserCourse();
  var addFavCourseView = new _fav_course.AddFavCourseView({
    favCourse: userCourse
  });

  // FIXME(david): Don't show if someone already has a fav course selected
  $('#add-fav-course-placeholder').replaceWith(addFavCourseView.render().el);

});
