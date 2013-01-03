// TODO(mack): there's some kind of require.js dependency issue that currently
// requires the 'user_course' module to be included here (probably of delayed
// require('user_course') in the 'course' module); need to investigate further
require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'user', 'course',
'user_course', 'schedule', 'facebook'],
function($, _, _s, _user, _course, _user_course, _schedule, _facebook) {

  _user.UserCollection.addToCache(pageData.userObjs);
  _course.CourseCollection.addToCache(pageData.courseObjs);

  // Render the schedule
  $schedulePlaceholder = $("#class-schedule-placeholder");
  var scheduleItems = new _schedule.ScheduleItemCollection(
    pageData.scheduleItemObjs);
  var scheduleView = _schedule.initScheduleView({
    scheduleItems: scheduleItems,
    width: $schedulePlaceholder.outerWidth()
  });
  $schedulePlaceholder.replaceWith(scheduleView.el);

  _facebook.initConnectButton({
    $button: $('.fbconnect-btn'),
    source: 'VIEW_FULL_PROFILE_SCHEDULE_PAGE',
    nextUrl: '/profile/' + pageData.profileUserId.$oid
  });

  mixpanel.track('Impression: Schedule page');
});
