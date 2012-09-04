define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'term', 'course'],
function($, _, _s, term, course) {

  /**
   * Parses transcript text. Will throw exception on failure to parse.
   * @param {string} data Transcript text
   * @return {TermCollection} Collection of TermModels
   */
  function parseTranscript(data) {
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
    //var program = _s.trim(matches[1]);

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

    var termCollection = new term.TermCollection();
    // Parse out the term and courses taken in that term
    _.each(termsRaw, function(termRaw) {
      matches = termRaw.match(/^((?:Spring|Fall|Winter) \d{4})/);
      var termName = matches[0];
      termRaw = termRaw.substring(termName.length);
      matches = termRaw.match(/[A-Z]+ \d{3}[A-Z]?/g);
      // TODO(mack): filter non-courses from matches
      if (matches) {
        var courseCollection = new course.CourseCollection();
        _.each(matches, function(courseId) {
          courseCollection.add({
            id: courseId
          });
        });
        termCollection.add({
          name: termName,
          courseCollection: courseCollection
        });
      }
    });

    return termCollection;
  }

  return {
    parseTranscript: parseTranscript
  };
});
