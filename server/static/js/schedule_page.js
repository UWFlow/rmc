require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'user', 'schedule'],
function($, _, _s, _user, _schedule) {

  _user.UserCollection.addToCache(pageData.userObjs);

  // Render the schedule
  $schedulePlaceholder = $("#class-schedule-placeholder");
  var scheduleItems = new _schedule.ScheduleItemCollection(
    pageData.scheduleItemObjs);
  var scheduleView = _schedule.initScheduleView({
    scheduleItems: scheduleItems,
    width: $schedulePlaceholder.outerWidth()
  });
  $schedulePlaceholder.replaceWith(scheduleView.el);

  mixpanel.track('Impression: Profile page');
});
