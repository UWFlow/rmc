define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'ext/bootstrap', 'util', 'ext/toastr'],
function(RmcBackbone, $, _, _s, ratings, __, util, jqSlide, _prof, toastr) {

  // TODO(jlfwong): Integrate models somehow
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
      this.$el.html(this.template({
        item: this.item
      }));

      return this;
    },

    resize: function(options) {
      var width = options.width;
      var hourHeight = options.hourHeight;

      var sv = this.scheduleView;

      var minuteHeight = hourHeight / 60.0;
      var startOffset = sv.startHour * hourHeight;

      var start = this.item.start;
      var end = this.item.end;

      var startTop = (start[0] * 60 + start[1]) * minuteHeight - startOffset;
      var endTop = (end[0] * 60 + end[1]) * minuteHeight - startOffset;

      this.$el.css({
        width: width,
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
      this.scheduleView = options.scheduleView;

      this.itemViews = [];
    },

    render: function() {
      this.$el.html(this.template({
        day: this.day
      }));


      var $scheduleItemContainer = this.$(".schedule-item-container");

      var self = this;
      _.each(this.day.items, function(item) {
        var itemView = new ScheduleItemView({
          item: item,
          scheduleDayView: self,
          scheduleView: self.scheduleView
        });
        $scheduleItemContainer.append(itemView.render().el);
        self.itemViews.push(itemView);
      });

      return this;
    },

    resize: function(options) {
      var width = options.width;
      var height = options.height;
      var headerHeight = options.headerHeight;
      var hourHeight = options.hourHeight;

      this.$el.css({
        width: width
      });

      this.$('.header').css({
        height: headerHeight
      });

      _.each(this.itemViews, function(itemView) {
        itemView.resize({
          hourHeight: hourHeight,
          width: width
        });
      });

      return this;
    }
  });

  var ScheduleHourLabelView = RmcBackbone.View.extend({
    template: _.template($("#schedule-hour-label-tpl").html()),

    className: 'hour-label',

    initialize: function(options) {
      this.hour = options.hour;
    },

    render: function() {
      this.$el.html(this.template({
        hour: this.hour
      }));

      return this;
    },

    resize: function(options) {
      var height = options.height;

      this.$el.css({
        height: height
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

      this.dayViews = [];
      this.hourLabelViews = [];
    },

    render: function() {
      this.$el.html(this.template({
        schedule: this.schedule
      }));

      var $dayContainer = this.$(".day-container");

      // TODO(jlfwong): Weekends?
      var dayNames = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday"
      ];

      var self = this;
      _.each(this.schedule.days, function(day, i) {
        day.name = dayNames[i];
        var dayView = new ScheduleDayView({
          day: day,
          scheduleView: self
        });
        $dayContainer.append(dayView.render().el);
        self.dayViews.push(dayView);
      });

      var $hourLabelContainer = this.$(".hour-label-container");

      for (var i = this.startHour; i <= this.endHour; i++) {
        var hourLabelView = new ScheduleHourLabelView({
          hour: i
        });
        $hourLabelContainer.append(hourLabelView.render().el);
        this.hourLabelViews.push(hourLabelView);
      }

      return this;
    },

    resize: function(options) {
      var height = options.height;
      var width = options.width;
      var headerHeight = options.headerHeight;
      var hourLabelWidth = options.hourLabelWidth;

      var nHours = this.endHour - this.startHour + 1;
      var hourHeight = (height - headerHeight) / nHours;

      this.$el.css({
        width: this.width,
        height: this.height
      });

      this.$('.times')
        .css({
          width: hourLabelWidth
        })
        .find('.header')
          .css({
            height: headerHeight
          });

      var nDays = this.schedule.days.length;
      var dayWidth = (width - hourLabelWidth) / nDays;

      _.each(this.dayViews, function(dayView) {
        dayView.resize({
          width: dayWidth,
          height: height,
          headerHeight: headerHeight,
          hourHeight: hourHeight
        });
      });

      _.each(this.hourLabelViews, function(hourLabelView) {
        hourLabelView.resize({height: hourHeight});
      });

      return this;
    }
  });

  // TODO(jlfwong): Remove me - move to profile.js and make data come from
  // models instead of arguments passed directly to the view

  var scheduleView = new ScheduleView({
    startHour: 6,
    endHour: 22,

    schedule: {
      days: [{
        items: [
          {
            start: [14, 30],
            end: [15, 50]
          },
          {
            start: [16, 0],
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
  })
  .render()
  .resize({
    headerHeight: 30,
    height: 600,

    hourLabelWidth: 100,
    width: 968
  });

  $("#class-schedule-placeholder").replaceWith(scheduleView.el);
});
