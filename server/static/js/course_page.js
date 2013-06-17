require(
['ext/jquery','course', 'took_this', 'user', 'tips', 'prof', 'exam', 'ratings',
'user_course', 'review', 'sign_in'],
function($, course, tookThis, user, tips, prof, _exam, ratings, user_course, _review, _sign_in) {

  course.CourseCollection.addToCache(pageData.courseObj);
  user_course.UserCourses.addToCache(pageData.userCourseObjs);
  prof.ProfCollection.addToCache(pageData.professorObjs);

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
  $('#course-inner-container').html(courseInnerView.render().el);
  courseInnerView.animateBars();

  if (window.pageData.examObjs.length) {
    var examCollection = new _exam.ExamCollection(window.pageData.examObjs);

    // Only show this "final exams" section if there are actually exams taking
    // place in the future
    if (examCollection.latestExam().get('end_date') >= new Date()) {
      var examSchedule = new _exam.ExamSchedule({
        exams: examCollection,
        last_updated_date: window.pageData.examUpdatedDate
      });
      var courseExamScheduleView = new _exam.CourseExamScheduleView({
        examSchedule: examSchedule
      });

      $('#exam-info-container')
        .html(courseExamScheduleView.render().el)
        .show();
    }
  }

  var tookThisSidebarView = new tookThis.TookThisSidebarView({
    userCourses: courseModel.get('friend_user_courses'),
    courseCode: courseModel.get('code'),
    currentTermId: window.pageData.currentTermId
  });
  $('#took-this-sidebar-container').html(tookThisSidebarView.render().el);

  if (window.pageData.tipObjs && pageData.tipObjs.length) {
    var tipsCollection = new _review.ReviewCollection(window.pageData.tipObjs);
    var tipsView = new tips.ExpandableTipsView({ reviews: tipsCollection });
    $('#tips-collection-container').replaceWith(tipsView.render().el);
  }

  // TODO(david): Handle no professors for course
  var profsCollection = courseModel.get('professors');
  var profsView = new prof.ProfCollectionView({ collection: profsCollection });
  $('#professor-review-container').html(profsView.render().el);

  if (!window.pageData.currentUserId) {
    _sign_in.renderBanner({
      fbConnectText: 'See friends taking this course!',
      source: 'BANNER_COURSE_PAGE',
      nextUrl: window.location.href
    });
  }

  mixpanel.track('Impression: Single course page');

  $(document.body).trigger('pageScriptComplete');
});
