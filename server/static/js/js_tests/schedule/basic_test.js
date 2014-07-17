define(function(require) {
  var expect = require('ext/chai').expect;
  var $ = require('ext/jquery');
  var schedule_parser = require('schedule_parser');

  describe('Schedule parsing', function() {
    var parsedSchedulePromise = $.get(
        '/static/js/js_tests/schedule/data/basic.txt').then(function(r) {
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

    testParsedScheduleAsync('extracts the term name',
        function(scheduleData) {
      expect(scheduleData.term_name).to.equal('Winter 2014');
    });

    testParsedScheduleAsync('produces correct number of courses',
        function(scheduleData) {
      expect(scheduleData.courses.length).to.equal(7);
    });

    testParsedScheduleAsync('produces no failed courses',
        function(scheduleData) {
      expect(scheduleData.failed_courses.length).to.equal(0);
    });

    testParsedScheduleAsync(
        'validate course that has multiple class and slot items',
        function(scheduleData) {
      expect(scheduleData.courses[1].course_id).to.equal('ece106');
      expect(scheduleData.courses[1].items.length).to.equal(63);
      expect(scheduleData.courses[1].items[0].section_type).to.equal('LEC');
      expect(scheduleData.courses[1].items[43].section_type).to.equal('LEC');
      expect(scheduleData.courses[1].items[44].section_type).to.equal('TUT');
      expect(scheduleData.courses[1].items[56].section_type).to.equal('TUT');
      expect(scheduleData.courses[1].items[57].section_type).to.equal('LAB');
      expect(scheduleData.courses[1].items[62].section_type).to.equal('LAB');
    });

    testParsedScheduleAsync('extracts the first course\'s course ID',
        function(scheduleData) {
      expect(scheduleData.courses[0].course_id).to.equal('cs138');
    });

    testParsedScheduleAsync(
        'extracts the correct number of items for course with one time entry',
        function(scheduleData) {
      expect(scheduleData.courses[0].items.length).to.equal(39);
    });

    testParsedScheduleAsync('extracts the first item\'s building',
        function(scheduleData) {
      expect(scheduleData.courses[0].items[0].building).to.equal('OPT');
    });

    testParsedScheduleAsync('extracts the first item\'s prof name',
        function(scheduleData) {
      expect(scheduleData.courses[0].items[0].prof_name).to
          .equal('Michael Godfrey');
    });

    testParsedScheduleAsync('extracts the first item\'s start date',
        function(scheduleData) {
      expect(scheduleData.courses[0].items[0].start_date).to.equal(1389106800);
    });

    testParsedScheduleAsync('extracts the first item\'s end date',
        function(scheduleData) {
      expect(scheduleData.courses[0].items[0].end_date).to.equal(1389111600);
    });

    testParsedScheduleAsync('extracts the first item\'s class number',
        function(scheduleData) {
      expect(scheduleData.courses[0].items[0].class_num).to.equal('5819');
    });

    testParsedScheduleAsync('extracts the first item\'s room',
        function(scheduleData) {
      expect(scheduleData.courses[0].items[0].room).to.equal('347');
    });

    testParsedScheduleAsync('extracts the first item\'s section number',
        function(scheduleData) {
      expect(scheduleData.courses[0].items[0].section_num).to.equal('001');
    });

    testParsedScheduleAsync('extracts the first item\'s section type',
        function(scheduleData) {
      expect(scheduleData.courses[0].items[0].section_type).to.equal('LEC');
    });

    testParsedScheduleAsync('extracts the last item\'s course ID',
        function(scheduleData) {
      expect(scheduleData.courses[6].course_id).to.equal('stat230');
    });

    testParsedScheduleAsync(
        'extracts the correct number of items for last course',
        function(scheduleData) {
      expect(scheduleData.courses[6].items.length).to.equal(54);
    });

    testParsedScheduleAsync('extracts the last item\'s building',
        function(scheduleData) {
      expect(scheduleData.courses[6].items[53].building).to.equal('DC');
    });

    testParsedScheduleAsync('extracts the last item\'s prof name',
        function(scheduleData) {
      expect(scheduleData.courses[6].items[53].prof_name).to
          .equal('Christian Boudreau');
    });

    testParsedScheduleAsync('extracts the last item\'s start date',
        function(scheduleData) {
      expect(scheduleData.courses[6].items[53].start_date).to.equal(1396629000);
    });

    testParsedScheduleAsync('extracts the last item\'s end date',
        function(scheduleData) {
      expect(scheduleData.courses[6].items[53].end_date).to.equal(1396632000);
    });

    testParsedScheduleAsync('extracts the last item\'s class number',
        function(scheduleData) {
      expect(scheduleData.courses[6].items[53].class_num).to.equal('7208');
    });

    testParsedScheduleAsync('extracts the last item\'s room',
        function(scheduleData) {
      expect(scheduleData.courses[6].items[53].room).to.equal('1350');
    });

    testParsedScheduleAsync('extracts the last item\'s section number',
        function(scheduleData) {
      expect(scheduleData.courses[6].items[53].section_num).to.equal('002');
    });

    testParsedScheduleAsync('extracts the last item\'s section type',
        function(scheduleData) {
      expect(scheduleData.courses[6].items[53].section_type).to.equal('LEC');
    });
  });
});
