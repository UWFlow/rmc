require(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'transcript'],
function(Backbone, $, _, _s, transcript) {
  $(function() {
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

      // Try/catch around parsing logic so that we show error message
      // should anything go wrong
      try {

        var terms = transcript.parseTranscript(data);

        // Add the parsed term and course info to the page for live preview
        _.each(terms, function(courses, termName) {
          // TODO(mack): move into backbone template
          var $term = $('<li class="term"/>');
          var $termName = $(_.sprintf('<h2 class="term">%s</h2>', termName));
          $term.append($termName);
          var $courses = $('<ul class="courses"/>');
          _.each(courses, function(courseCode) {
            var $course = $(_.sprintf('<li class="course">%s</li>', courseCode));
            $courses.append($course);
          });
          $term.append($courses);
          $('#terms').append($term);
        });

      } catch (ex) {
        console.log('ex', ex.toString());
        $('#transcript-error').text(
            'Could not extract course information. '
            + 'Please check that you\'ve pasted the transcript correctly.');
      }
    });

    // Handle the case that the user inputs into the transcript text area
    // before the page has finished loading.
    if ($transcript.val()) {
      $transcript.trigger('input');
    }
  });
});
