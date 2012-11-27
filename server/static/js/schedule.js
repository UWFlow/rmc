define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'ext/bootstrap', 'util', 'ext/toastr'],
function(RmcBackbone, $, _, _s, ratings, __, util, jqSlide, _prof, toastr) {

  var ScheduleItem = RmcBackbone.Model.extend({
    start: function() {
      var x = this.get('time').split(' - ');
      var start = x[0];
      return start.split(':');
    },

    end: function() {
      var x = this.get('time').split(' - ');
      var end = x[1];
      return end.split(':');
    }
  });

  var ScheduleDay = RmcBackbone.Collection.extend({
  });

  var Schedule = RmcBackbone.Collection.extend({
  });

  var ScheduleItemView = RmcBackbone.View.extend({
    template: _.template($("#schedule-item-tpl").html()),

    className: 'schedule-item',

    initialize: function(options) {
      this.item = options.item;
      this.width = options.width;
      this.scheduleView = options.scheduleView;
      this.scheduleDayView = options.scheduleDayView;
    },

    render: function() {
      var sv = this.scheduleView;

      var nHours = sv.endHour - sv.startHour + 1;
      var hourHeight = (sv.height - sv.headerHeight) / nHours;
      var minuteHeight = hourHeight / 60.0;
      var startOffset = sv.startHour * hourHeight;

      this.$el.html(this.template({
        item: this.item
      }));

      var start = this.item.start;
      var end = this.item.end;

      var startTop = (start[0] * 60 + start[1]) * minuteHeight - startOffset;
      var endTop = (end[0] * 60 + end[1]) * minuteHeight - startOffset;

      this.$el.css({
        width: this.width,
        top: startTop,
        height: endTop - startTop
      });

      return this;
    }
  });

  var ScheduleDayView = RmcBackbone.View.extend({
    template: _.template($("#schedule-day-tpl").html()),

    className: 'day',

    initialize: function(options) {
      this.day = options.day;
      this.width = options.width;
      this.scheduleView = options.scheduleView;
    },

    render: function() {
      this.$el.html(this.template({
        day: this.day
      }));


      var width = this.width;

      this.$el.css({
        width: width
      });

      var $scheduleItemContainer = this.$(".schedule-item-container");

      var self = this;
      _.each(this.day.items, function(item) {
        $scheduleItemContainer.append(new ScheduleItemView({
          item: item,
          width: width,
          scheduleDayView: self,
          scheduleView: self.scheduleView
        }).render().el);
      });

      return this;
    }
  });

  var ScheduleHourLabelView = RmcBackbone.View.extend({
    template: _.template($("#schedule-hour-label-tpl").html()),

    className: 'hour-label',

    initialize: function(options) {
      this.hour = options.hour;
      this.height = options.height;
    },

    render: function() {
      this.$el.html(this.template({
        hour: this.hour
      }));

      this.$el.css({
        height: this.height
      });

      return this;
    }
  });

  // TODO(jlfwong): Resizing

  var ScheduleView = RmcBackbone.View.extend({
    template: _.template($("#schedule-tpl").html()),

    className: 'class-schedule',

    initialize: function(options) {
      this.scheduleWeek = options.scheduleWeek;
      this.schedule = options.schedule;
      this.startHour = options.startHour;
      this.endHour = options.endHour;
      this.width = options.width;
      this.height = options.height;
      this.headerHeight = options.headerHeight;
      this.hourLabelWidth = options.hourLabelWidth;
    },

    render: function() {
      this.$el.html(this.template({
        schedule: this.schedule
      }));

      this.$el.css({
        width: this.width,
        height: this.height
      });

      var $dayContainer = this.$(".day-container");

      // TODO(jlfwong): Weekends?
      var dayNames = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday"
      ];

      var nDays = this.schedule.days.length;
      var dayWidth = (this.width - this.hourLabelWidth) / nDays;

      var self = this;
      _.each(this.schedule.days, function(day, i) {
        day.name = dayNames[i];
        $dayContainer.append(new ScheduleDayView({
          day: day,
          width: dayWidth,
          scheduleView: self
        }).render().el);
      });

      var $hourLabelContainer = this.$(".hour-label-container");

      var nHourLabels = this.endHour - this.startHour + 1;
      var hourLabelHeight = (this.height - this.headerHeight) / nHourLabels;

      for (var i = this.startHour; i <= this.endHour; i++) {
        $hourLabelContainer.append(new ScheduleHourLabelView({
          hour: i,
          height: hourLabelHeight
        }).render().el);
      }

      this.$('.header').css({
        height: this.headerHeight
      });

      this.$('.times').css({
        width: this.hourLabelWidth
      });

      return this;
    }
  });

  // TODO: Remove me
    $("#class-schedule-placeholder").replaceWith(new ScheduleView({
      startHour: 6,
      endHour: 22,

      headerHeight: 30,
      height: 600,

      hourLabelWidth: 100,
      width: 968,

      schedule: {
        days: [{
          items: [
            {
              start: [14, 30],
              end: [15, 50]
            },
            {
              start: [16, 00],
              end: [17, 20]
            }
          ]
        }, {
          items: [
          ]
        }, {
          items: [
            {
              start: [8, 30],
              end: [9, 20]
            }
          ]
        }, {
          items: [
          ]
        }, {
          items: [
          ]
        }]
      }
    }).render().el);
});
