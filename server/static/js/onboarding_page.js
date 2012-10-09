require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'transcript',
'util'],
function($, _, _s, transcript, util) {

  var $transcript = $('#transcript-text');

  $transcript.bind('input paste', function(evt) {
    console.log('input paste');
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
    console.log('called addTranscriptData');
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
        window.location.href = '/profile';
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
