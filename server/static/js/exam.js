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
    }
  });

  var ExamCollection = RmcBackbone.Collection.extend({
    model: Exam,

    comparator: function(exam) {
      return exam.get('start_date').$date;
    },

    groupedByCourse: function() {
      return this.chain()
        .groupBy(function(model) { return model.get('course_id'); })
        .sortBy(function(exams) { return exams[0].get('start_date').$date; })
        .value();
    }
  });

  var ExamSchedule = RmcBackbone.Model.extend({
    defaults: {
      exams: new ExamCollection([null, null, null, null, null]),
      // TODO(david): 2013
      term_name: 'Fall 2012'
    }
  });

  var ExamScheduleView = RmcBackbone.View.extend({
    template: _.template($('#exam-schedule-tpl').html()),
    className: 'exam-schedule',

    initialize: function(options) {
      this.examSchedule = options.examSchedule;
    },

    render: function() {
      this.$el.html(this.template(this.examSchedule.toJSON()));
      return this;
    }
  });

  return {
    Exam: Exam,
    ExamCollection: ExamCollection,
    ExamSchedule: ExamSchedule,
    ExamScheduleView: ExamScheduleView
  };
});
