define(function(require) {
  var expect = require('ext/chai').expect;
  var transcript = require('transcript');
  var $ = require('ext/jquery');

  describe('Transcript parsing', function() {
    var parsedTranscriptPromise = $.get(
        '/static/js/js_tests/transcript/data/basic.txt').then(function(r) {
      return transcript.parseTranscript(r);
    });

    var testParsedTranscriptAsync = function(testName, callback) {
      it(testName, function(done) {
        parsedTranscriptPromise.then(function(transcriptData) {
          try {
            callback(transcriptData);
            done();
          } catch (e) {
            return done(e);
          }
        });
      });
    };

    testParsedTranscriptAsync('extracts the student number',
        function(transcriptData) {
      expect(transcriptData.studentId).to.equal(20331374);
    });

    testParsedTranscriptAsync('extracts the program name',
        function(transcriptData) {
      expect(transcriptData.programName).to.equal(
          'Software Engineering, Honours, Co-operative Program');
    });

    testParsedTranscriptAsync('extracts the number of terms',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm.length).to.equal(10);
    });

    testParsedTranscriptAsync('extracts the oldest term\'s courses',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[9].courseIds).to.have.members([
        'che102', 'cs137', 'math115', 'math117', 'phys115', 'se101'
      ]);
    });

    testParsedTranscriptAsync('extracts the oldest term\'s name',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[9].name).to.equal('Fall 2009');
    });

    testParsedTranscriptAsync('extracts the oldest term\'s programYearId',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[9].programYearId).to.equal('1A');
    });

    testParsedTranscriptAsync('extracts the most recent term\'s courses',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[0].courseIds).to.have.members([
        'cs343', 'cs348', 'earth121', 'earth121l', 'se390', 'se463', 'wkrpt300'
      ]);
    });

    testParsedTranscriptAsync('extracts the most recent term\'s name',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[0].name).to.equal('Fall 2012');
    });

    testParsedTranscriptAsync('extracts the most recent term\'s programYearId',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[0].programYearId).to.equal('3B');
    });
  });
});
