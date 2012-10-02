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

  // TODO(mack): do this in a cleaner way
  var interest = courseModel.get('ratings').find(function(rating) {
    return rating.get('name') === 'interest';
  });
  var ratingBoxView = new ratings.RatingBoxView({
    model: interest
  });
  $('#rating-box-container').html(ratingBoxView.render().el);

  // TODO(mack): remove duplication with logic in course.js
  if (!userCourse && pageData.currentUserId) {
    // TODO(mack): remove require()
    // TODO(mack): should we really be creating a user_course if
    // the user has no taken the course?
    userCourse = new user_course.UserCourse({
      course_id: this.courseModel.get('id'),
      user_id: pageData.currentUserId.$oid
    });
    this.courseModel.set('user_course', this.userCourse);
  }
  var courseInnerView = new course.CourseInnerView({
    courseModel: courseModel,
    userCourse: userCourse
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
