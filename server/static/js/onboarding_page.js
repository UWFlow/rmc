require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'transcript',
'util'],
function($, _, _s, transcript, util) {

  var $transcript = $('#transcript-text');

  // Log events for manually importing courses button clicks
  $("#manual-course-import-button").click(function(evt) {
    // TODO(Sandy): Add fbid as the label
    _gaq.push([
      '_trackEvent',
      'USER_GENERIC',
      'WANT_MANUAL_COURSE_IMPORTING'
    ]);
  });

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

    // TODO(Sandy): This assumes the /transcript request will succeed and that
    // google's servers are faster than ours, which may not be the case. But if
    // we make this request in the success handler, it might not get logged at
    // all (due to the redirect). We could setTimeout the redirect, but that
    // would cause delay and also since /transcript should just be succesful,
    // we'll do this for now. Maybe move to server side
    _gaq.push([
      '_trackEvent',
      'USER_GENERIC',
      'TRANSCRIPT_UPLOAD'
    ]);
    mixpanel.track('Transcript uploaded');
    $.post(
      '/api/transcript',
      {
        'transcriptData': JSON.stringify(transcriptData)
      },
      function() {
        // TODO(mack): load and update page with js rather than reloading
        // Fail safe to make sure at least we sent off the _gaq trackEvent
        _gaq.push(function() {
          var redirectUrl = util.getQueryParam('next');
          if (redirectUrl) {
            window.location.href = redirectUrl;
          } else {
            window.location.href = '/profile';
          }
        });
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

  mixpanel.track('Impression: Onboarding page');
});
