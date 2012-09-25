require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'transcript',
'term', 'course', 'friend', 'util', 'user'],
function($, _, _s, transcript, term, course, friend, util, user) {

  // Render friend sidebar

  (function() {
    var userCollection = new user.UserCollection(
      window.pageData.profileObj.friends);
    userCollection.each(function(userModel) {
      userModel.set('coursesTook',
        new course.CourseCollection(userModel.get('coursesTook')));
      userModel.set('mutual_courses',
        new course.CourseCollection(userModel.get('mutual_courses')));
    });
    var friendSidebarView = new friend.FriendSidebarView({
      friendCollection: userCollection
    });
    $('#friend-sidebar-container').html(friendSidebarView.render().el);
  })();

  var renderTranscript = function(transcriptData) {
    var termCollection = new term.TermCollection();

    _.each(transcriptData, function(termData) {
      var termModel = new term.TermModel({
        name: termData.term_name,
        program_year_id: termData.program_year_id,
        courseCollection: new course.CourseCollection(termData.course_models)
      });
      termCollection.add(termModel);
    });

    // Add the parsed term and course info to the page for live preview
    var termCollectionView = new term.TermCollectionView({
      termCollection: termCollection
    });
    $('#term-collection-container').html(termCollectionView.render().el).show();

    transcript_remove_text = $('#transcript-remove-text')
      .html('<a id="remove-transcript-link">Remove my transcript!</a>')
      .show();
    $('#remove-transcript-link').click(function(event) {
      event.preventDefault();
      // TODO(Sandy): Ask for confirmation?

      $.post('/api/remove_transcript', {}, function(response) {
        // TODO(Sandy: Make duration dependent on the # of courses the user has
        duration = 1500;
        term_collection_container = $('#term-collection-container')
          .fancySlide('up', duration);
        transcript_remove_text.fadeOut(duration);

        setTimeout(function() {
          term_collection_container.html('');
          transcript_remove_text.html('');
        }, duration);
      });
    });
  }

  // Render the transcript, if available
  transcriptData = window.pageData.transcriptData
  if (transcriptData && transcriptData.length != 0) {
    renderTranscript(transcriptData)
  }

  var $transcript = $('#transcript-text');

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
    try {

      var transcriptData = transcript.parseTranscript(data);
      var coursesByTerm = transcriptData.coursesByTerm;
    } catch (ex) {
      $('#transcript-error').text(
          'Could not extract course information. ' +
          'Please check that you\'ve pasted the transcript correctly.');
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
        // TODO(mack): load and update page with js rather th reloading
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
});
