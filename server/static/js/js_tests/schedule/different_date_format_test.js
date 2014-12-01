define(function(require) {
  var expect = require('ext/chai').expect;
  var $ = require('ext/jquery');
  var schedule_parser = require('schedule_parser');

  describe('Schedule parsing (different date format)', function() {
    var parsedSchedulePromise = $.get(
        '/static/js/js_tests/schedule/data/different_date_format.txt'
      ).then(function(r) {
        return schedule_parser.parseSchedule(r);
      }
    );

    var testParsedScheduleAsync = function(testName, testCallback) {
      it(testName, function(done) {
        parsedSchedulePromise.then(function(scheduleData) {
          try {
            testCallback(scheduleData);
            done();
          } catch (e) {
            return done(e);
          }
        });
      });
    };

    testParsedScheduleAsync('extracts the first item\'s start date',
        function(scheduleData) {
      expect(scheduleData.courses[0].items[0].start_date).to.equal(1389106800);
    });

    testParsedScheduleAsync('extracts the first item\'s end date',
        function(scheduleData) {
      expect(scheduleData.courses[0].items[0].end_date).to.equal(1389111600);
    });

    testParsedScheduleAsync('extracts the last item\'s start date',
        function(scheduleData) {
      expect(scheduleData.courses[6].items[53].start_date).to.equal(1396629000);
    });

    testParsedScheduleAsync('extracts the last item\'s end date',
        function(scheduleData) {
      expect(scheduleData.courses[6].items[53].end_date).to.equal(1396632000);
    });
  });
});
