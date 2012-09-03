$(function() {
  var $transcript = $('#transcript-text');
  $transcript.bind('input paste', function(evt) {
    // Remove any old info from the page
    $('#terms').empty();

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

      var beginMarker = 'UNIVERSITY  OF  WATERLOO  UNDERGRADUATE  UNOFFICIAL  TRANSCRIPT';
      var endMarker = 'End of Transcript';

      var beginIndex = data.indexOf(beginMarker);
      if (beginIndex !== -1) {
        beginIndex += beginMarker.length; }
      var endIndex = data.indexOf(endMarker);
      if (endIndex === -1) {
        endIndex = data.length;
      }
      // Set portion of transcript that we care about to be between
      // begin and end markers
      data = data.substring(beginIndex, endIndex);

      // TODO(mack): utilize studentId and program information
      //var matches = data.match(/Student ID: (\d+)/)
      //var studentId = parseInt(matches[1], 10);
      //matches = data.match(/Program: (.*?)[\n]/);
      //var program = _.trim(matches[1]);

      var termsRaw = [];

      var termRe = /Spring|Fall|Winter/g;
      var match = termRe.exec(data);
      var lastIndex = -1;
      // Split the transcript by terms
      while (match) {
        if (lastIndex !== -1) {
          termsRaw.push(data.substring(lastIndex, match.index));
        }
        lastIndex = match.index;
        match = termRe.exec(data);
      }
      if (lastIndex) {
        termsRaw.push(data.substring(lastIndex));
      }

      var terms = {};
      // Parse out the term and courses taken in that term
      _.each(termsRaw, function(termRaw) {
        matches = termRaw.match(/^((?:Spring|Fall|Winter) \d{4})/);
        var termName = matches[0];
        termRaw = termRaw.substring(termName.length);
        matches = termRaw.match(/[A-Z]+ \d{3}[A-Z]?/g);
        // TODO(mack): filter non-courses from matches
        if (matches) {
          terms[termName] = matches;
        }
      });

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
