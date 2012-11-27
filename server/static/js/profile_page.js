require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'transcript',
'term', 'course', 'friend', 'util', 'user', 'user_course', 'prof', 'exam',
'raffle_unlock', 'schedule'],
function($, _, _s, transcript, term, course, friend, util, user, uc, _prof,
    _exam, _raffle_unlock, _schedule) {

  user.UserCollection.addToCache(pageData.userObjs);
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
      friendCollection: userCollection,
      raffleSupervisor: _raffle_unlock.getRaffleSupervisor()
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

  var $transcript = $('#transcript-text');

  var examObjs = window.pageData.examObjs;
  if (examObjs && examObjs.length) {
    var examCollection = new _exam.ExamCollection(window.pageData.examObjs);
    // TODO(david): 2013
    var examSchedule = new _exam.ExamSchedule({
      exams: examCollection
    });
    var examScheduleView = new _exam.ExamScheduleView({
      examSchedule: examSchedule
    });
    $('#exam-schedule-placeholder').replaceWith(examScheduleView.render().el);
  }

  $transcript.bind('input paste', function(evt) {
    // Remove any old info from the page
    $('#terms').empty();
    $('#transcript-error').empty();

    // Store the transcript text
    var data = $(evt.currentTarget).val();
    if (!data) {
      // If the text area has been emptied, exit immediately w/o
      // showing error message for parse failure.
      return;
    }

    addTranscriptData(data);
  });

  var addTranscriptData = function(data) {
    // Try/catch around parsing logic so that we show error message
    // should anything go wrong
    var transcriptData;
    var coursesByTerm;
    try {
      transcriptData = transcript.parseTranscript(data);
      coursesByTerm = transcriptData.coursesByTerm;
    } catch (ex) {
      console.warn('Could not parse transcript', ex);
      $('#transcript-error').text(
          'Uh oh. Could not parse your transcript :( ' +
          'Please check that you\'ve pasted your transcript correctly.');
      return;
    }

    // TODO(mack): fix confusing names between term/termObj and course/courseObj
    var courseIds = [];
    _.each(coursesByTerm, function(termObj) {
      _.each(termObj.courseIds, function(courseId) {
        courseIds.push(courseId);
      });
    });

    $.post(
      '/api/transcript',
      {
        'transcriptData': JSON.stringify(transcriptData)
      },
      function() {
        // TODO(mack): load and update page with js rather than reloading
        window.location.reload();
      },
      'json'
    );
  };

  // Handle the case that the user inputs into the transcript text area
  // before the page has finished loading.
  if ($transcript.val()) {
    $transcript.trigger('input');
  }

  var init = function() {
    if (util.getQueryParam('test')) {
      $.get('/static/sample_transcript.txt', function(data) {
        addTranscriptData(data);
      });
    }
  };

  init();

  // Render the schedule if possible
  if (pageData.scheduleItemObjs.length > 0) {
    var scheduleItems = new _schedule.ScheduleItemCollection(
      pageData.scheduleItemObjs);

    window.x = scheduleItems;

    var scheduleView = new _schedule.ScheduleView({
      startHour: 8,
      endHour: 18,
      scheduleItems: scheduleItems
    });

    scheduleView
      .render()
      .resize({
        headerHeight: 30,
        height: 800,

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
  }

  mixpanel.track('Impression: Profile page');
});
