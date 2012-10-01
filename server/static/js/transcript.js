define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string'],
function($, _, _s) {

  /**
   * Parses transcript text. Will throw exception on failure to parse.
   * @param {string} data Transcript text
   * @return {array} list of { termName: <X>, courseIds: [<A>, <B>, ...] } objects
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
    var matches = data.match(/Student ID: (\d+)/);
    var studentId = parseInt(matches[1], 10);
    matches = data.match(/Program: (.*?)[\n]/);
    var programName = _s.trim(matches[1]);

    var termsRaw = [];

    var termRe = /Spring|Fall|Winter/g;
    var match = termRe.exec(data);
    var lastIndex = -1;
    // Split the transcript by terms
    while (match) {
      if (lastIndex !== -1) {
        var termRaw = data.substring(lastIndex, match.index);
        termsRaw.push(termRaw);
      }
      lastIndex = match.index;
      match = termRe.exec(data);
    }
    if (lastIndex) {
      termsRaw.push(data.substring(lastIndex));
    }

    var coursesByTerm = [];
    // Parse out the term and courses taken in that term
    _.each(termsRaw, function(termRaw, i) {
      var matches = termRaw.match(/^((?:Spring|Fall|Winter) \d{4})\s+(\d[A-B])/);
      if (!matches) {
        // This could happen for a term that is a transfer from another school
        return;
      }

      var termName = matches[1];
      var programYearId = matches[2];
      termRaw = termRaw.substring(termName.length);
      matches = termRaw.match(/[A-Z]+ \d{3}[A-Z]?/g);
      var courseIds = [];
      // TODO(mack): filter non-courses from matches
      if (matches) {
        _.each(matches, function(courseId) {
          courseId = courseId.replace(/\s+/g, '').toLowerCase();
          courseIds.push(courseId);
        });
        coursesByTerm.push({
          name: termName,
          programYearId: programYearId,
          courseIds: courseIds
        });
      }
    });

    return {
      coursesByTerm: coursesByTerm,
      studentId: studentId,
      programName: programName
    };
  }

  return {
    parseTranscript: parseTranscript
  };
});
