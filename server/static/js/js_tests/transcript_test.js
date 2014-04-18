/* global it, describe */

define(function(require) {
  var expect = require('chai').expect;
  var transcript = require('transcript');
  var $ = require('jquery');

  describe('Transcript parsing', function() {
    var parsedTranscriptPromise = $.get(
        '/sample_transcript.txt').then(function(r) {
      return transcript.parseTranscript(r);
    });


    it('extracts the student number', function(done) {
      parsedTranscriptPromise.then(function(transcriptData) {
        expect(transcriptData.studentId).to.equal(20331374);
        done();
      });
    });

    it('extracts the program name',function(done) {
      parsedTranscriptPromise.then(function(transcriptData) {
        expect(transcriptData.programName).to.equal(
            'Software Engineering, Honours, Co-operative Program');
        done();
      });
    });

    it('extracts the number of terms',function(done) {
      parsedTranscriptPromise.then(function(transcriptData) {
        expect(transcriptData.coursesByTerm.length).to.equal(10);
        done();
      });
    });

    it('extracts the oldest term\'s courses', function(done) {
      parsedTranscriptPromise.then(function(transcriptData) {
        expect(transcriptData.coursesByTerm[9].courseIds).to.have.members([
          'che102', 'cs137', 'math115', 'math117', 'phys115', 'se101'
        ]);
        done();
      });
    });

    it('extracts the oldest term\'s name', function(done) {
      parsedTranscriptPromise.then(function(transcriptData) {
        expect(transcriptData.coursesByTerm[9].name).to.equal('Fall 2009');
        done();
      });
    });

    it('extracts the oldest term\'s programYearId', function(done) {
      parsedTranscriptPromise.then(function(transcriptData) {
        expect(transcriptData.coursesByTerm[9].programYearId).to.equal('1A');
        done();
      });
    });

    it('extracts the most recent term\'s courses', function(done) {
      parsedTranscriptPromise.then(function(transcriptData) {
        expect(transcriptData.coursesByTerm[0].courseIds).to.have.members([
          'cs343', 'cs348', 'earth121', 'earth121l', 'se390', 'se463',
          'wkrpt300'
        ]);
        done();
      });
    });

    it('extracts the most recent term\'s name', function(done) {
      parsedTranscriptPromise.then(function(transcriptData) {
        expect(transcriptData.coursesByTerm[0].name).to.equal('Fall 2012');
        done();
      });
    });

    it('extracts the most recent term\'s programYearId', function(done) {
      parsedTranscriptPromise.then(function(transcriptData) {
        expect(transcriptData.coursesByTerm[0].programYearId).to.equal('3B');
        done();
      });
    });
  });
});
