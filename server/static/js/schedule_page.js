// TODO(mack): there's some kind of require.js dependency issue that currently
// requires the 'user_course' module to be included here (probably of delayed
// require('user_course') in the 'course' module); need to investigate further
require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'user', 'course',
'user_course', 'schedule', 'facebook', 'sign_in', 'util'],
function($, _, _s, _user, _course, _user_course, _schedule, _facebook,
  _sign_in, _util) {

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

  var profileUser = _user.UserCollection.getFromCache(pageData.profileUserId.$oid);
  if (_util.getQueryParam('v') === 'full_profile') {
    var fbConnectText = _s.sprintf(
        'View %s\'s full profile!', profileUser.get('first_name'));
    _sign_in.renderBannerIfNecessary({
      source: 'FULL_PROFILE_BANNER_SCHEDULE_PAGE',
      fbConnectText: fbConnectText,
      nextUrl: _s.sprintf('/profile/%s', profileUser.id)
    });
  } else {
    _sign_in.renderBannerIfNecessary({
      source: 'SHARE_SCHEDULE_BANNER_SCHEDULE_PAGE',
      fbConnectText: 'Share your schedule too!'
    });
  }

  if (_util.getQueryParam('print')) {
    $('#schedule-print-css').attr('media', 'screen,print');

    window.print();

    mixpanel.track('Impression: Print schedule page');
  } else {
    mixpanel.track('Impression: Schedule page');
  }

});
