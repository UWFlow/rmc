require(
['ext/jquery','course', 'took_this', 'user', 'tips', 'prof', 'ratings',
'user_course'],
function($, course, tookThis, user, tips, prof, ratings, user_course) {
  // TODO(david): Customize with people who took this course.
  courseIds = ['CS137', 'SCI238', 'CS241'];

  var courseData = window.pageData.data;
  var courseModel = new course.CourseModel(courseData);

  var ratingBoxView = new ratings.RatingBoxView({
    model: new ratings.RatingModel(courseData.overall)
  });
  $('#rating-box-container').html(ratingBoxView.render().el);

  var courseInnerView = new course.CourseInnerView({
    courseModel: courseModel
  });
  $('#course-inner-placeholder').html(courseInnerView.render().el);
  courseInnerView.animateBars();

  var tookThisSidebarView = new tookThis.TookThisSidebarView({
    collection: new user_course.UserCourses(pageData.data.friend_user_courses),
    courseCode: courseModel.get('code')
  });
  $('#took-this-sidebar-container').html(tookThisSidebarView.render().el);

  // TODO(Sandy): Use the comment_date field
  tipsData = window.pageData.tips;
  var tipsCollection = new tips.TipsCollection(tipsData);

  var tipsView = new tips.ExpandableTipsView({ tips: tipsCollection });
  $('#tips-collection-placeholder').replaceWith(tipsView.render().el);

  // TODO(david): Handle no professors for course
  var profsCollection = new prof.ProfCollection(courseData.professors);
  var profsView = new prof.ProfCollectionView({ collection: profsCollection });
  $('#professor-review-container').html(profsView.render().el);

});
