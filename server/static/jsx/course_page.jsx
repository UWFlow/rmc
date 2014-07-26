/** @jsx React.DOM */
require(
['ext/jquery','course', 'took_this', 'user', 'tips', 'prof', 'exam', 'ratings',
  'user_course', 'review', 'sign_in', 'ext/react', 'util', 'moment',
  'react_components'],
function($, course, tookThis, user, tips, prof, _exam, ratings, user_course,
    _review, _sign_in, React, util, moment, rc) {

  course.CourseCollection.addToCache(pageData.courseObj);
  user_course.UserCourses.addToCache(pageData.userCourseObjs);
  prof.ProfCollection.addToCache(pageData.professorObjs);

  var courseObj = pageData.courseObj;
  var courseModel = course.CourseCollection.getFromCache(courseObj.id);
  var userCourse = courseModel.get('user_course');

  var overallRating = courseModel.getOverallRating();
  var ratingBoxView = new ratings.RatingBoxView({ model: overallRating });
  $('#rating-box-container').html(ratingBoxView.render().el);
  console.log(courseModel);
  var courseInnerView = new course.CourseInnerView({
    courseModel: courseModel,
    userCourse: userCourse,
    shouldLinkifySectionProfs: true
  });
  //  $('#course-inner-container').html(courseInnerView.render().el);
  //courseInnerView.animateBars();

   React.renderComponent(
      <rc.CourseInnerView data={courseModel.attributes} />,
      document.getElementById('course-inner-container')
    );

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

  React.renderComponent(
    <rc.ReviewBox data={window.pageData.tipObjs} />,
    document.getElementById('tips-collection-container')
  );

  React.renderComponent(
    <rc.ProfCollection data={window.pageData.professorObjs} />,
    document.getElementById('professor-review-container')
  );


  // TODO(david): Handle no professors for course
  //$('#professor-review-container').html(profsView.render().el);

  if (!window.pageData.currentUserId) {
    _sign_in.renderBanner({
      source: 'BANNER_COURSE_PAGE',
      nextUrl: window.location.href
    });
  }

  mixpanel.track('Impression: Single course page');

  $(document.body).trigger('pageScriptComplete');
});
