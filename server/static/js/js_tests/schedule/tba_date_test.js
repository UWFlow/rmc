define(function(require) {
  var expect = require('ext/chai').expect;
  var $ = require('ext/jquery');
  var schedule_parser = require('schedule_parser');

  describe('Schedule parsing', function() {
    var parsedSchedulePromise = $.get(
        '/static/js/js_tests/schedule/data/tba_date.txt').then(function(r) {
      return schedule_parser.parseSchedule(r);
    });

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

    testParsedScheduleAsync('produces correct number of courses',
        function(scheduleData) {
      expect(scheduleData.courses.length).to.equal(3);
    });

    testParsedScheduleAsync('produces no failed courses',
        function(scheduleData) {
      expect(scheduleData.failed_courses.length).to.equal(0);
    });

    testParsedScheduleAsync('extracts the first course\'s course ID',
        function(scheduleData) {
      expect(scheduleData.courses[0].course_id).to.equal('coop4');
    });

    testParsedScheduleAsync('checks there are no schedule items for course',
        function(scheduleData) {
      expect(scheduleData.courses[0].items.length).to.equal(0);
    });
  });
});
