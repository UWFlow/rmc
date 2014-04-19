define(function(require) {
  var expect = require('chai').expect;
  var $ = require('jquery');
  var schedule_parser = require('schedule_parser');

  describe('Schedule parsing', function() {
    var parsedSchedulePromise = $.get(
        '/sample_schedule.txt').then(function(r) {
      return schedule_parser.parseSchedule(r);
    });

    it('extracts the term name', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.term_name).to.equal("Winter 2014");
        done();
      });
    });

    it('produces no failed items', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.failed_items.length).to.equal(0);
        done();
      });
    });

    it('extracts the correct number of items', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items.length).to.equal(343);
        done();
      });
    });

    it('extracts the first item\'s building', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items[0].building).to.equal("OPT");
        done();
      });
    });

    it('extracts the first item\'s course ID', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items[0].course_id).to.equal("cs138");
        done();
      });
    });

    it('extracts the first item\'s prof name', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items[0].prof_name).to.equal(
            "Michael Godfrey");
        done();
      });
    });

    it('extracts the first item\'s start date', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items[0].start_date).to.equal(
            1389106800);
        done();
      });
    });

    it('extracts the first item\'s end date', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items[0].end_date).to.equal(
            1389111600);
        done();
      });
    });

    it('extracts the last item\'s building', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items[342].building).to.equal("DC");
        done();
      });
    });

    it('extracts the last item\'s course ID', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items[342].course_id).to.equal(
            "stat230");
        done();
      });
    });

    it('extracts the last item\'s prof name', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items[342].prof_name).to.equal(
            "Christian Boudreau");
        done();
      });
    });

    it('extracts the last item\'s start date', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items[342].start_date).to.equal(
            1396629000);
        done();
      });
    });

    it('extracts the last item\'s end date', function(done) {
      parsedSchedulePromise.then(function(scheduleData) {
        expect(scheduleData.processed_items[342].end_date).to.equal(
            1396632000);
        done();
      });
    });
  });
});
