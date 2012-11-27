define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ratings', 'ext/bootstrap', 'util', 'ext/toastr'],
function(RmcBackbone, $, _, _s, ratings, __, util, jqSlide, _prof, toastr) {

  var strTimeToMinutes = function(strTime) {
    // Given a string in 24 hour HH:MM format, returns the corresponding number
    // of minutes since the beginning of the day
    var x = strTime.split(':');
    return parseInt(x[0], 10) * 60 + parseInt(x[1], 10);
  };

  // TODO(jlfwong): Integrate models somehow
  var ScheduleItem = RmcBackbone.Model.extend({
    startMinutes: function() {
      return strTimeToMinutes(this.get('start_time'));
    },

    endMinutes: function() {
      return strTimeToMinutes(this.get('end_time'));
    }
  });

  var ScheduleItemCollection = RmcBackbone.Collection.extend({
    model: ScheduleItem,

    forDay: function(day) {
      return new ScheduleItemCollection(this.filter(function(x) {
        return _.indexOf(x.get('days'), day) !== -1;
      }));
    },

    byDay: function() {
      return [
        this.forDay('M'),
        this.forDay('T'),
        this.forDay('W'),
        this.forDay('Th'),
        this.forDay('F')
      ];
    }
  });

  // CSS constants
  var headerPadding = 8;
  var headerBorderHeight = 0;

  var ScheduleItemView = RmcBackbone.View.extend({
    template: _.template($("#schedule-item-tpl").html()),

    className: 'schedule-item',

    initialize: function(options) {
      this.scheduleItem = options.scheduleItem;
      this.width = options.width;
      this.scheduleView = options.scheduleView;
      this.scheduleDayView = options.scheduleDayView;
    },

    render: function() {
      this.$el
        .html(this.template(this.scheduleItem.toJSON()))
        .addClass('well');

      return this;
    },

    resize: function(options) {
      var width = options.width;
      var hourHeight = options.hourHeight;

      var sv = this.scheduleView;

      var minuteHeight = hourHeight / 60.0;
      var startOffset = sv.startHour * hourHeight;

      var startMinutes = this.scheduleItem.startMinutes();
      var endMinutes = this.scheduleItem.endMinutes();

      var startTop = startMinutes * minuteHeight - startOffset;
      var endTop = endMinutes * minuteHeight - startOffset;

      // NOTE: Not a real CSS margin since the item is absolutely positioned
      var margin = 2;
      var borderWidth = 1;
      var padding = 8;

      this.$el.css({
        width: width - 2 * margin - 2 * borderWidth - 2 * padding,
        left: margin,
        top: Math.floor(startTop),
        height: Math.floor(endTop - startTop) - 2 * borderWidth - 2 * padding
      });

      return this;
    }
  });

  var ScheduleDayView = RmcBackbone.View.extend({
    template: _.template($("#schedule-day-tpl").html()),

    className: 'day',

    initialize: function(options) {
      this.day = options.day;
      this.scheduleItems = options.scheduleItems;
      this.scheduleView = options.scheduleView;

      this.itemViews = [];
    },

    render: function() {
      this.$el.html(this.template({
        day: this.day
      }));

      var $scheduleItemContainer = this.$(".schedule-item-container");

      var self = this;
      this.scheduleItems.each(function(scheduleItem) {
        var itemView = new ScheduleItemView({
          scheduleItem: scheduleItem,
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

      var borderWidth = 1;

      this.$el.css({
        width: width - borderWidth,
        height: height
      });

      this.$('.header').css({
        height: headerHeight - 2 * headerPadding - headerBorderHeight
      });

      _.each(this.itemViews, function(itemView) {
        itemView.resize({
          hourHeight: hourHeight,
          width: width - borderWidth
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

      var borderHeight = 1;
      var padding = 8;

      this.$el.css({
        height: height - 2 * padding - borderHeight
      });

      return this;
    }
  });

  // TODO(jlfwong): Resizing

  var ScheduleView = RmcBackbone.View.extend({
    template: _.template($("#schedule-tpl").html()),

    className: 'class-schedule',

    initialize: function(options) {
      this.startHour = options.startHour;
      this.endHour = options.endHour;

      this.scheduleItems = options.scheduleItems;

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
      _.each(this.scheduleItems.byDay(), function(itemsForDay, i) {
        var dayView = new ScheduleDayView({
          day: {
            name: dayNames[i]
          },
          scheduleItems: itemsForDay,
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
      var hourHeight = Math.floor((height - headerHeight) / nHours);

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
            height: headerHeight - 2 * headerPadding - headerBorderHeight
          });

      // TODO(jlfwong): Don't know if we need to support weekends anytime
      // soon...
      var nDays = 5;

      // TODO(jlfwong): Rounding error's a bitch. Figure out a cleaner way of
      // dealing with this (pad days until they fill the full space)
      var dayWidth = Math.floor((width - hourLabelWidth) / nDays);

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

  return {
    ScheduleItem: ScheduleItem,
    ScheduleItemCollection: ScheduleItemCollection,
    ScheduleView: ScheduleView
  };
});
