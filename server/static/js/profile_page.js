require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'transcript',
'term'],
function($, _, _s, transcript, term) {
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

      var termCollection = undefined;
      // Try/catch around parsing logic so that we show error message
      // should anything go wrong
      try {
        termCollection = transcript.parseTranscript(data);
      } catch (ex) {
        console.log('ex', ex.toString());
        $('#transcript-error').text(
            'Could not extract course information. '
            + 'Please check that you\'ve pasted the transcript correctly.');
        return;
      }

      // Add the parsed term and course info to the page for live preview
      var termCollectionView = new term.TermCollectionView({
        termCollection: termCollection
      });
      $('#term-collection-container').html(termCollectionView.render().el);
    });

    // Handle the case that the user inputs into the transcript text area
    // before the page has finished loading.
    if ($transcript.val()) {
      $transcript.trigger('input');
    }
  });
});
