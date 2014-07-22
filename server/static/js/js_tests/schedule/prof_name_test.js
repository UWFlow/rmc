define(function(require) {
  var expect = require('ext/chai').expect;
  var $ = require('ext/jquery');
  var schedule_parser = require('schedule_parser');

  describe('Schedule parsing', function() {
    var parsedSchedulePromise = $.get(
        '/static/js/js_tests/schedule/data/prof_name.txt').then(function(r) {
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
      expect(scheduleData.courses.length).to.equal(5);
    });

    testParsedScheduleAsync('produces no failed courses',
        function(scheduleData) {
      expect(scheduleData.failed_courses.length).to.equal(0);
    });

    testParsedScheduleAsync('checks that MATH 137 parsed as expected',
        function(scheduleData) {
      expect(scheduleData.courses[3].course_id).to.equal('math137');
      expect(scheduleData.courses[3].items[0].prof_name).to
          .equal('Serge D\'Alessio');
      expect(scheduleData.courses[3].items.length).to.equal(38);
      expect(scheduleData.courses[3].items[0].section_type).to.equal('LEC');
      expect(scheduleData.courses[3].items[37].section_type).to.equal('TST');
    });
  });
});
