// TODO(mack): there's some kind of require.js dependency issue that currently
// requires the 'user_course' module to be included here (probably of delayed
// require('user_course') in the 'course' module); need to investigate further
require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'user', 'course',
'user_course', 'schedule', 'facebook', 'sign_in', 'util', 'rmc_moment'],
function($, _, _s, _user, _course, _user_course, _schedule, _facebook,
  _sign_in, _util, moment) {

  _user.UserCollection.addToCache(pageData.userObjs);
  _course.CourseCollection.addToCache(pageData.courseObjs);

  // Render the schedule
  var $schedulePlaceholder = $("#class-schedule-placeholder");
  var scheduleItems = new _schedule.ScheduleItemCollection(
    pageData.scheduleItemObjs);

  var schedule = new _schedule.Schedule({ schedule_items: scheduleItems });
  var scheduleView = _schedule.initScheduleView({
    schedule: schedule,
    scheduleItems: scheduleItems,
    width: $schedulePlaceholder.outerWidth()
  });
  $schedulePlaceholder.replaceWith(scheduleView.el);

  var profileUser = _user.UserCollection.getFromCache(
      pageData.profileUserId.$oid);
  if (!window.pageData.currentUserId) {
    _sign_in.renderBanner({
      source: 'SHARE_SCHEDULE_BANNER_SCHEDULE_PAGE',
      nextUrl: '/profile?import-schedule=1'
    });
  }

  if (!pageData.currentUserId) {
    $('.view-profile-btn').click(function(evt) {
      var firstName = profileUser.get('first_name');
      _sign_in.renderModal({
        title: 'Only ' + firstName + '\'s friends can view his profile',
        message: 'Verify that you are friends with ' + firstName,
        source: 'MODAL_FRIENDS_TAKEN',
        nextUrl: '/profile/' + profileUser.id
      });
    });
  }

  // TODO(jlfwong): Make the page URL push-state change with the query param
  // changing as you change the current week.
  var startDate = _util.getQueryParam('start_date');
  if (startDate) {
    schedule.setWeek(new Date(Number(startDate)));
  }

  if (_util.getQueryParam('print')) {
    // Brand the schedule a bit
    $('<img src="/static/img/flow-logo-75x35.png">')
      .css({
        float: 'right',
        height: 25
      })
      .appendTo('.class-schedule .schedule-nav');

    window.print();

    mixpanel.track('Impression: Print schedule page');
  } else {
    mixpanel.track('Impression: Schedule page');
  }

  $(document.body).trigger('pageScriptComplete');
});
