require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'term', 'course', 'friend', 'util', 'user', 'user_course', 'prof', 'exam',
'raffle_unlock', 'schedule'],
function($, _, _s, _bootstrap, term, course, friend, util, user, uc, _prof,
    _exam, _raffle_unlock, _schedule) {

  course.CourseCollection.addToCache(pageData.courseObjs);
  uc.UserCourses.addToCache(pageData.userCourseObjs);
  _prof.ProfCollection.addToCache(pageData.professorObjs);

  var profileUser = user.UserCollection.getFromCache(
    pageData.profileUserId.$oid);
  var currentUser;
  if (pageData.currentUserId) {
    currentUser = user.UserCollection.getFromCache(
      pageData.currentUserId.$oid);
  }

  // Render friend sidebar
  (function() {
    // TODO(mack): use profileUser.get('friends')
    var friendIds = profileUser.get('friend_ids');
    var friendObjs = [];
    _.each(friendIds, function(friendId) {
      var friendObj = user.UserCollection.getFromCache(friendId);
      friendObjs.push(friendObj);
    });
    var userCollection = new user.UserCollection(friendObjs);

    userCollection.comparator = function(user) {
      return -user.get('mutual_courses').length;
    };

    userCollection.sort();

    var friendSidebarView = new friend.FriendSidebarView({
      currentUser: currentUser,
      friendCollection: userCollection
    });

    $('#friend-sidebar-container').html(friendSidebarView.render().el);
  })();

  var renderTranscript = function(transcriptObj) {
    var termCollection = new term.TermCollection();

    _.each(transcriptObj, function(termObj) {
      var termModel = new term.TermModel(termObj);
      termCollection.add(termModel);
    });

    // Add the parsed term and course info to the page for live preview
    var termCollectionView = new term.TermCollectionView({
      termCollection: termCollection
    });
    $('#term-collection-container')
      .html(termCollectionView.render().el)
      .prepend('<h1>Courses</h1>')  // TODO(david): This should be in HTML
      .show();
  };

  // Render the transcript, if available
  var transcriptObj = window.pageData.transcriptObj;
  if (transcriptObj && transcriptObj.length !== 0) {
    renderTranscript(transcriptObj);
  }

  var examObjs = window.pageData.examObjs;
  if (examObjs && examObjs.length) {
    var examCollection = new _exam.ExamCollection(window.pageData.examObjs);
    var examSchedule = new _exam.ExamSchedule({
      exams: examCollection
    });
    var examScheduleView = new _exam.ExamScheduleView({
      examSchedule: examSchedule
    });
    $('#exam-schedule-placeholder').replaceWith(examScheduleView.render().el);
  }

  // Render the schedule if possible
  if (pageData.scheduleItemObjs.length > 0) {
    var scheduleItems = new _schedule.ScheduleItemCollection(
      pageData.scheduleItemObjs);

    var scheduleView = new _schedule.ScheduleView({
      maxStartHour: 8,
      minEndHour: 18,
      scheduleItems: scheduleItems
    });

    scheduleView
      .render()
      .resize({
        headerHeight: 30,
        hourHeight: 60,
        hourLabelWidth: 100,
        width: $("#class-schedule-placeholder").outerWidth()
      });

    $(window).resize(function() {
      scheduleView.resize({
        headerHeight: 30,
        height: 800,

        hourLabelWidth: 100,
        width: scheduleView.$el.outerWidth()
      });
    });

    $("#class-schedule-placeholder").replaceWith(scheduleView.el);

    if (window.pageData.ownProfile) {
      var scheduleShareView = new _schedule.ScheduleShareView({
        url: _schedule.getPublicScheduleLink()
      });
      $("#schedule-share-placeholder").replaceWith(scheduleShareView.render().el);
    }
  }

  // Show the add schedule pop-up on a hash URL
  var showScheduleModal =
      (window.location.hash.indexOf('import-schedule') !== -1);

  if (window.pageData.showImportScheduleButton || showScheduleModal) {
    var scheduleInputModalView = new _schedule.ScheduleInputModalView();
    $('#schedule-input-modal-placeholder')
      .replaceWith(scheduleInputModalView.render().el);
  }

  if (showScheduleModal) {
    $('.schedule-input-modal').modal();
  }

  mixpanel.track('Impression: Profile page');
});
