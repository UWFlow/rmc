// TODO(mack): there's some kind of require.js dependency issue that currently
// requires the 'user_course' module to be included here (probably of delayed
// require('user_course') in the 'course' module); need to investigate further
define(
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

  var schedule = new _schedule.Schedule();
  var scheduleView = _schedule.initScheduleView({
    schedule: schedule,
    scheduleItems: scheduleItems,
    width: $schedulePlaceholder.outerWidth()
  });
  $schedulePlaceholder.replaceWith(scheduleView.el);

  var profileUser = _user.UserCollection.getFromCache(pageData.profileUserId.$oid);
  _sign_in.renderBannerIfNecessary({
    source: 'SHARE_SCHEDULE_BANNER_SCHEDULE_PAGE',
    fbConnectText: 'Connect with Facebook',
    nextUrl: '/profile?import-schedule=1'
  });

  // TODO(mack): pass the message through renderBannerIfNecessary()
  var $signinMessage = $('#sign-in-banner-container .message');
  $signinMessage.html(
    '...to <strong>create your own schedule</strong> and '+
    '<strong>see what friends are taking</strong>'
  );

  if (!pageData.currentUserId) {
    $('.view-profile-btn').click(function(evt) {
      var firstName = profileUser.get('first_name');
      _sign_in.renderModal({
        title: 'Only ' + firstName + '\'s friends can view his profile',
        message: 'Verify that you are friends with ' + firstName,
        fbConnectText: 'Connect with Facebook',
        source: 'MODAL_FRIENDS_TAKEN',
        nextUrl: '/profile/' + profileUser.id
      });
    });
  }

  if (_util.getQueryParam('print')) {
    var startDate = _util.getQueryParam('start_date');
    if (startDate) {
      schedule.set('start_date', new Date(Number(startDate)));
    }
    var endDate = _util.getQueryParam('end_date');
    if (endDate) {
      schedule.set('end_date', new Date(Number(endDate)));
    }

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

});
