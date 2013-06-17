define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'course'],
function(RmcBackbone, $, _, _course) {

  var Exam = RmcBackbone.Model.extend({
    defaults: {
      course_id: 'cs137',
      sections: '001,002',
      start_date: new Date(2012, 11, 11, 19),
      end_date: new Date(2012, 11, 11, 21),
      location: 'M3 1006,MC 4020,4021,4045',
      location_known: true,
      info_known: true,
      url: ''
    },

    referenceFields: {
      course: ['course_id', _course.CourseCollection]
    },

    getCourseCode: function() {
      var course = this.get('course');
      return course ? course.get('code') : this.get('course_id');
    }
  });

  var ExamCollection = RmcBackbone.Collection.extend({
    model: Exam,

    comparator: function(exam) {
      return exam.get('start_date');
    },

    groupedByCourse: function() {
      return this.chain()
        .groupBy(function(model) { return model.get('course_id'); })
        .sortBy(function(exams) { return exams[0].get('start_date'); })
        .value();
    },

    latestExam: function() {
      return this.last();
    }
  });

  var ExamSchedule = RmcBackbone.Model.extend({
    defaults: {
      exams: new ExamCollection([null, null, null, null, null]),
      last_updated_date: null
    }
  });

  var ExamScheduleView = RmcBackbone.View.extend({
    className: 'exam-schedule',

    initialize: function(options) {
      this.examSchedule = options.examSchedule;
      this.template = _.template($('#exam-schedule-tpl').html());

      this.examScheduleTableView = new ExamScheduleTableView({
        examSchedule: this.examSchedule,
        showCourseCode: true
      });
    },

    render: function() {
      this.$el.html(this.template(this.examSchedule.toJSON()));
      this.$('.exam-schedule-table-placeholder')
        .replaceWith(this.examScheduleTableView.render().el);
      return this;
    }
  });

  var CourseExamScheduleView = RmcBackbone.View.extend({
    className: 'exam-schedule',

    initialize: function(options) {
      this.examSchedule = options.examSchedule;
      this.template = _.template($('#course-exam-schedule-tpl').html());

      this.examScheduleTableView = new ExamScheduleTableView({
        examSchedule: this.examSchedule,
        showCourseCode: false
      });
    },

    render: function() {
      this.$el.html(this.template(this.examSchedule.toJSON()));
      this.$('.exam-schedule-table-placeholder')
        .replaceWith(this.examScheduleTableView.render().el);
      return this;
    }
  });

  var ExamScheduleTableView = RmcBackbone.View.extend({
    className: 'course-exam-schedule-table',

    initialize: function(options) {
      this.templateOptions = {
        showCourseCode: !!options.showCourseCode
      };
      this.examSchedule = options.examSchedule;
      this.template = _.template($('#exam-schedule-table-tpl').html());
    },

    render: function() {
      this.$el.html(this.template(
        _.extend(this.templateOptions, this.examSchedule.toJSON())
      ));

      return this;
    }
  });

  return {
    Exam: Exam,
    ExamCollection: ExamCollection,
    ExamSchedule: ExamSchedule,
    ExamScheduleView: ExamScheduleView,
    CourseExamScheduleView: CourseExamScheduleView
  };
});
