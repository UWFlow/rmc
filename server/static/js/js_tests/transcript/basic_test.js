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
      expect(transcriptData.studentId).to.equal(20705374);
    });

    testParsedTranscriptAsync('extracts the program name',
        function(transcriptData) {
      expect(transcriptData.programName).to.equal(
          'Computer Science/Digital Hardware Option, ' +
          'Honours, Co-operative Program'
      );
    });

    testParsedTranscriptAsync('extracts the number of terms',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm.length).to.equal(5);
    });

    testParsedTranscriptAsync('extracts the oldest term\'s courses',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[4].courseIds).to.have.members([
        'cs145', 'math145', 'math147', 'psych101', 'spcom223'
      ]);
    });

    testParsedTranscriptAsync('extracts the oldest term\'s name',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[4].name).to.equal('Fall 2017');
    });

    testParsedTranscriptAsync('extracts the oldest term\'s programYearId',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[4].programYearId).to.equal('1A');
    });

    testParsedTranscriptAsync('extracts the most recent term\'s courses',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[0].courseIds).to.have.members([
        'coop2', 'pd10', 'wkrpt200m'
      ]);
    });

    testParsedTranscriptAsync('extracts the most recent term\'s name',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[0].name).to.equal('Winter 2019');
    });

    testParsedTranscriptAsync('extracts the most recent term\'s programYearId',
        function(transcriptData) {
      expect(transcriptData.coursesByTerm[0].programYearId).to.equal('2B');
    });
  });
});
