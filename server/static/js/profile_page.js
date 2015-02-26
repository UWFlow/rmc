require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'term', 'course', 'friend', 'util', 'user', 'user_course', 'prof', 'exam',
'raffle_unlock', 'schedule', 'sign_in', 'work_queue', 'scholarship',
'ext/react'],
function($, _, _s, _bootstrap, term, _course, friend, _util, user, _user_course,
  _prof, _exam, _raffle_unlock, _schedule, _sign_in, _work_queue,
  _scholarship, React) {

  _course.CourseCollection.addToCache(pageData.courseObjs);
  _user_course.UserCourses.addToCache(pageData.userCourseObjs);
  _prof.ProfCollection.addToCache(pageData.professorObjs);

  var profileUser = user.UserCollection.getFromCache(
    pageData.profileUserId.$oid);

  var currentUser;
  if (pageData.currentUserId) {
    currentUser = user.UserCollection.getFromCache(
      pageData.currentUserId.$oid);
  }

  // Show the add schedule pop-up on a hash URL
  var showScheduleModal = !!_util.getQueryParam('import-schedule');

  // For demo account, cancel some AJAX calls on this page and pop-up a log-in
  // dialog
  if (window.location.pathname === '/profile/demo') {
    $.ajaxSetup({
      beforeSend: function(jqXhr, settings) {
        if (_(['PUT', 'POST', 'DELETE']).contains(settings.type) &&
            settings.url !== '/login/facebook') {
          _sign_in.renderModal({
            source: 'MODAL_DEMO_PROFILE_AJAX',
            nextUrl: window.location.origin
          });
          return false;
        }
      }
    });

    _sign_in.renderBanner({
      source: 'BANNER_DEMO_PROFILE_PAGE',
      nextUrl: window.location.origin,
      message: ('This is a demo account; nothing is saved.<br>When you\'re ' +
        'done playing...')
    });
  }

  // Add in Scholarship stuff (Jeff)
  React.render(React.createElement(_scholarship.ScholarshipContainer,
    {scholarshipData: pageData.scholarshipObjs}),
    document.getElementById('scholarship-placeholder'));

  var scheduleInputModalView = new _schedule.ScheduleInputModalView();
  $('#schedule-input-modal-placeholder')
    .replaceWith(scheduleInputModalView.render().el);
  $('#schedule-teaser').click(function() {
    $('.schedule-input-modal').modal();
  });
  $('#import-schedule-heading').click(function() {
    $('.schedule-input-modal').modal();
  });

  // By default, setting data-target on the button takes too
  // long before the button click listener is bound, so
  // manually bind the click listener
  $('.schedule-input-btn').click(function(evt) {
    $('.schedule-input-modal').modal();
  });

  if (showScheduleModal) {
    $('.schedule-input-modal').modal();
  }

    // Render the schedule if possible
  if (pageData.scheduleItemObjs.length > 0) {
    _work_queue.add(function() {
      var scheduleItems = new _schedule.ScheduleItemCollection(
        pageData.scheduleItemObjs);

      var $schedulePlaceholder = $("#class-schedule-placeholder");
      var scheduleView = _schedule.initScheduleView({
        scheduleItems: scheduleItems,
        failedScheduleItems: window.pageData.failedScheduleItemObjs,
        width: $schedulePlaceholder.outerWidth(),
        showSharing: window.pageData.ownProfile
      });
      $schedulePlaceholder.replaceWith(scheduleView.el);
    });
  }

  var renderTranscript = function(transcriptObj) {
    var termCollection = new term.TermCollection();

    _.each(transcriptObj, function(termObj) {
      var termModel = new term.TermModel(termObj);
      termCollection.add(termModel);
    });

    // Add the parsed term and course info to the page for live preview
    var profileTermsView = new term.ProfileTermsView({
      termCollection: termCollection,
      showAddTerm: window.pageData.ownProfile
    });
    $('#profile-terms-placeholder').replaceWith(profileTermsView.render().el);
  };

  // Render the transcript, if available
  var transcriptObj = window.pageData.transcriptObj;
  if (transcriptObj && transcriptObj.length !== 0) {
    _work_queue.add(function() {
      renderTranscript(transcriptObj);
    });
  }

  var examObjs = window.pageData.examObjs;
  if (examObjs && examObjs.length) {
    _work_queue.add(function() {
      var examCollection = new _exam.ExamCollection(window.pageData.examObjs);

      // Only show this "final exams" section if there are actually exams taking
      // place in the future
      if (examCollection.latestExam().get('end_date') >= new Date()) {
        var examSchedule = new _exam.ExamSchedule({
          exams: examCollection,
          last_updated_date: window.pageData.examUpdatedDate
        });
        var examScheduleView = new _exam.ExamScheduleView({
          examSchedule: examSchedule
        });
        $('#exam-schedule-placeholder').replaceWith(
          examScheduleView.render().el);
      }
    });
  }

  _work_queue.add(function() {
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

    if (userCollection.length > 0) {
      $('#friend-sidebar-container').html(friendSidebarView.render().el);
    }

    // Show "add to shortlist" alert if not previously dismissed
    var hideShortlistAlertKey = 'hide-shortlist-alert';
    var $shortlistAlert = $('#shortlist-alert');
    if ($shortlistAlert.length && !_util.getLocalData(hideShortlistAlertKey)){
      $shortlistAlert
        .slideDown("fast")
        .on('close.bs.alert', function() {
          // Remember the alert was dismissed
          _util.storeLocalData(hideShortlistAlertKey, true,
              /* expiration */ +new Date() + (1000 * 60 * 60 * 24 * 30 * 3));
        });
    }
  });

  $('#referral-alert .referral-link-box').bind('click', function(evt) {
    $(this).select();
  });

  // Possibly show a modal pop-up to prompt user to review course
  window.setTimeout(function() {
    if (window.pageData.courseIdToReview ||
        _util.getQueryParam('review_modal')) {
      // TODO(david): This should be encapsulated in a convenience fn in
      // user_course.js
      var courseId = window.pageData.courseIdToReview;
      var reviewModal = new _user_course.ReviewModalView({
        courseId: courseId
      });
      if (courseId) {
        reviewModal.render().show();
      }
    }
  }, 1000);

  mixpanel.track('Impression: Profile page');

  $(document.body).trigger('pageScriptComplete');
});
