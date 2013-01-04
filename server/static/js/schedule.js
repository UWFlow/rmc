define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap', 'course', 'util', 'facebook'],
function(RmcBackbone, $, _, _s, _bootstrap, _course, _util, _facebook) {

  var strTimeToMinutes = function(strTime) {
    // Given a string in 24 hour HH:MM format, returns the corresponding number
    // of minutes since the beginning of the day
    var x = strTime.split(':');
    return parseInt(x[0], 10) * 60 + parseInt(x[1], 10);
  };

  var ScheduleItem = RmcBackbone.Model.extend({
    referenceFields: {
      'course': ['course_id', _course.CourseCollection]
    },

    intersects: function(otherItem) {
      var selfStart = this.startMinutes();
      var selfEnd = this.endMinutes();
      var otherStart = otherItem.startMinutes();
      var otherEnd = otherItem.endMinutes();
      return (otherStart >= selfStart && otherStart <= selfEnd) ||
        (otherEnd >= selfStart && otherEnd <= selfEnd) ||
        // To capture the case that self is enclosed by other
        (selfStart >= otherStart && selfStart <= otherEnd) ||
        // This check is not needed, but just for symmetry it's here
        (selfEnd >= otherStart && selfEnd <= otherEnd);
    },

    startMinutes: function() {
      return strTimeToMinutes(this.get('start_time'));
    },

    endMinutes: function() {
      return strTimeToMinutes(this.get('end_time'));
    }
  });

  var ScheduleItemCollection = RmcBackbone.Collection.extend({
    model: ScheduleItem,

    comparator: function(firstItem, secondItem) {
      var firstStart = firstItem.startMinutes();
      var secondStart = secondItem.startMinutes();
      if (firstStart === secondStart) {
        // If they have the same start time, the longer item should be first
        if (firstItem.endMinutes() >= secondItem.endMinutes()) {
          return -1;
        } else {
          return 1;
        }
      } else if (firstStart < secondStart) {
        return -1;
      } else {
        return 1;
      }
    },

    forDay: function(day) {
      var items = new ScheduleItemCollection(this.filter(function(x) {
        return _.indexOf(x.get('days'), day) !== -1;
      }));
      items.sort();
      return items;
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
      this.scheduleView = options.scheduleView;
      this.scheduleDayView = options.scheduleDayView;
    },

    getCssClass: function() {
      var section = String(this.scheduleItem.get('section'));
      var sectionType = /[a-zA-Z]{3}/.exec(section)[0];
      var cssClass = {
        LEC: 'blue',
        TUT: 'green',
        LAB: 'red',
        SEM: 'yellow',
        PRJ: 'purple'
      }[sectionType];

      // TODO(david): Actually hash the section type to get a color, to be more
      //     extensible to new unknown section type designations.
      return cssClass || 'gray';
    },

    render: function() {
      this.$el
        .html(this.template({
          item: this.scheduleItem
        }))
        .addClass('well')
        .addClass('truncate')
        .addClass(this.getCssClass());

      return this;
    },

    resize: function(options) {
      this.resizeOptions = options;

      var hourHeight = options.hourHeight;
      var leftOffset = options.leftOffset;
      var rightOffset = options.rightOffset;

      var sv = this.scheduleView;

      var minuteHeight = hourHeight / 60.0;
      var startOffset = sv.startHour * hourHeight;

      var startMinutes = this.scheduleItem.startMinutes();
      var endMinutes = this.scheduleItem.endMinutes();

      var startTop = startMinutes * minuteHeight - startOffset;
      var endTop = endMinutes * minuteHeight - startOffset;

      this.$el.css({
        left: leftOffset,
        right: rightOffset,
        top: Math.floor(startTop) - 1,
        height: Math.floor(endTop - startTop)
      });

      return this;
    },

    events: {
      'mouseenter': 'mouseenterView',
      'mouseleave': 'mouseleaveView'
    },

    mouseenterView: function(evt) {
      if (!this.resizeOptions) {
        return;
      }

      this.$el.removeClass('truncate');
      this.$el.css({
        'z-index': 1,
        'left': 0,
        'right': 0
      });
    },

    mouseleaveView: function(evt) {
      if (!this.resizeOptions) {
        return;
      }

      this.$el.addClass('truncate');
      this.$el.css({
        'z-index': ''
      });

      this.resize(this.resizeOptions);
    }
  });

  var ScheduleDayView = RmcBackbone.View.extend({
    template: _.template($("#schedule-day-tpl").html()),

    className: 'day',

    initialize: function(options) {
      this.day = options.day;
      this.scheduleItems = options.scheduleItems;
      this.scheduleView = options.scheduleView;

      this.itemViews = {};
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
        self.itemViews[scheduleItem.id] = itemView;
      });

      return this;
    },

    resize: function(options) {
      var height = options.height;
      var headerHeight = options.headerHeight;
      var hourHeight = options.hourHeight;

      this.$el.css({
        height: height
      });

      this.$('.header').css({
        height: headerHeight - 2 * headerPadding - headerBorderHeight
      });

      var position = 0;
      // Right now, only supporting 2 positions for intersecting schedule items:
      // left side and right side. A series of intersecting items will zigzag
      // between left and right.
      var numPositions = 2;

      for (var idx = 0; idx < this.scheduleItems.size(); ++idx) {
        var currScheduleItem = this.scheduleItems.at(idx);

        var prevScheduleItem = this.scheduleItems.at(idx - 1);
        var nextScheduleItem = this.scheduleItems.at(idx + 1);
        var intersects =
          (prevScheduleItem && prevScheduleItem.intersects(currScheduleItem)) ||
          (nextScheduleItem && nextScheduleItem.intersects(currScheduleItem));

        var leftOffset;
        var rightOffset;
        if (intersects) {
          // Deal with conflicts; currently only handles max of 2 intersecting
          // schedule items
          leftOffset = (position/numPositions * 100) + '%';
          rightOffset = (100 - ((position + 1) * 100/numPositions)) + '%';
          position = (position + 1) % numPositions;
        } else {
          position = 0;
          leftOffset = 0;
          rightOffset = 0;
        }

        var itemView = this.itemViews[currScheduleItem.id];
        itemView.resize({
          hourHeight: hourHeight,
          leftOffset: leftOffset,
          rightOffset: rightOffset
        });
      }

      return this;
    }
  });

  var ScheduleHourLabelView = RmcBackbone.View.extend({
    template: _.template($("#schedule-hour-row-tpl").html()),

    className: 'hour-row',

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

      this.$el.css({
        height: height - borderHeight
      });

      return this;
    }
  });

  // TODO(jlfwong): Resizing

  var ScheduleView = RmcBackbone.View.extend({
    template: _.template($("#schedule-tpl").html()),

    className: 'class-schedule',

    initialize: function(options) {
      this.startHour = options.maxStartHour;
      this.endHour = options.minEndHour;

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

      _.each(this.scheduleItems.byDay(), function(itemsForDay, i) {
        var dayView = new ScheduleDayView({
          day: {
            name: dayNames[i]
          },
          scheduleItems: itemsForDay,
          scheduleView: this
        });

        var minStartItem = itemsForDay.min(function(item) {
          return item.startMinutes();
        });
        if (minStartItem && minStartItem.startMinutes() / 60 < this.startHour) {
          this.startHour = Math.floor(minStartItem.startMinutes() / 60);
        }

        var maxEndItem = itemsForDay.max(function(item) {
          return item.endMinutes();
        });
        if (maxEndItem && maxEndItem.endMinutes() / 60 > this.endHour) {
          this.endHour = Math.ceil(maxEndItem.endMinutes() / 60);
        }

        $dayContainer.append(dayView.render().el);
        this.dayViews.push(dayView);
      }, this);

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
      var width = options.width;
      var hourHeight = options.hourHeight;
      var headerHeight = options.headerHeight;

      var nHours = this.endHour - this.startHour + 1;
      var height = hourHeight * nHours + headerHeight;

      this.$el.css({
        width: this.width,
        height: this.height
      });

      this.$('.times .header').css({
        height: headerHeight - 2 * headerPadding - headerBorderHeight
      });

      // TODO(jlfwong): Don't know if we need to support weekends anytime
      // soon...
      var nDays = 5;

      _.each(this.dayViews, function(dayView) {
        dayView.resize({
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

  var ScheduleInputView = RmcBackbone.View.extend({
    template: _.template($('#schedule-input-tpl').html()),

    className: 'schedule-input',

    events: {
      'input .schedule-input-textarea': 'inputSchedule',
      'paste .schedule-input-textarea': 'inputSchedule'
    },

    initialize: function() {
    },

    render: function() {
      this.$el.html(this.template({}));
      return this;
    },

    inputSchedule: function(evt) {
      this.$('.schedule-input-error').empty();

      // Store the schedule text
      var data = $(evt.currentTarget).val();
      if (!data) {
        // If the text area has been emptied, exit immediately w/o
        // showing error message for parse failure.
        return;
      }

      this.addScheduleData(data);
    },

    addScheduleData: function(data) {
      var scheduleData;
      try {
        scheduleData = parseSchedule(data);
        console.log('parsing success');
      } catch (ex) {
        $.ajax('/api/schedule/log', {
          data: {
            schedule: data
          },
          type: 'POST'
        });

        this.$('.schedule-input-error').text(
            'Uh oh. Could not parse your schedule :( ' +
            'Check that you\'ve pasted your schedule correctly.');

        mixpanel.track('Schedule parse error', { error_msg: ex.toString() });
        console.log('parsing fail');
        return;
      }
      console.log('after parse');
      _gaq.push([
        '_trackEvent',
        'USER_GENERIC',
        'SCHEDULE_UPLOAD'
      ]);
      mixpanel.track('Schedule uploaded');
      $.post(
        '/api/schedule', {
          'schedule_text': data,
          'schedule_data': JSON.stringify(scheduleData.processedItems),
          'term_name': scheduleData.termName
        }, function() {
          window.location.href = '/profile';
        },
        'json'
      );
    }
  });

  var ScheduleInputModalView = RmcBackbone.View.extend({
    template: _.template($('#schedule-input-modal-tpl').html()),

    initialize: function() {
      this.scheduleInputView = new ScheduleInputView();
    },

    render: function() {
      this.$el.html(this.template({}));
      this.$('.schedule-input-placeholder')
        .replaceWith(this.scheduleInputView.render().el);
      return this;
    }
  });

  var ScheduleShareView = RmcBackbone.View.extend({
    template: _.template($('#schedule-share-tpl').html()),

    className: 'schedule-share',

    initialize: function(options) {
      this.options = options;
    },

    events: {
      'click .facebook-btn': 'shareScheduleFacebook',
      'click .link-box': 'onFocus'
      // TODO(Sandy): Restore text after clicking away?
    },

    onFocus: function() {
      this.$('.link-box').select();
      this.logShareIntent('Link box');
    },

    shareScheduleFacebook: function() {
      _facebook.showFeedDialog(
        getPublicScheduleLink(),
        'My Winter 2013 class schedule',
        'on Flow',
        'Check out my Winter 2013 class schedule!',
        _.bind(function(response) {
          this.logShareCompleted('Facebook');
        }, this)
      );
      this.logShareIntent('Facebook');
    },

    logShareIntent: function(shareMethod) {
      mixpanel.track('Share schedule intent', {
        ShareMethod: shareMethod
      });
      mixpanel.people.increment({'Share schedule intent': 1});
    },

    logShareCompleted: function(shareMethod) {
      mixpanel.track('Share schedule completed', {
        ShareMethod: shareMethod
      });
      mixpanel.people.increment({'Share schedule completed': 1});
    },

    render: function() {
      this.$el.html(this.template(this.options));
      return this;
    }
  });

  var initScheduleView = function(options) {
    var width = options.width;
    var scheduleItems = options.scheduleItems;

    var scheduleView = new ScheduleView({
      maxStartHour: 8,
      minEndHour: 18,
      scheduleItems: scheduleItems
    });

    scheduleView
      .render()
      .resize({
        headerHeight: 30,
        hourHeight: 60,
        width: width
      });

    $(window).resize(function() {
      scheduleView.resize({
        headerHeight: 30,
        height: 800,
        width: scheduleView.$el.outerWidth()
      });
    });

    return scheduleView;
  };

  var getPublicScheduleLink = function() {
    return _util.getSiteBaseUrl() +
        '/schedule/' + window.pageData.currentUserId.$oid;
  };

  // TODO(jlfwong): Remove me - move to profile.js and make data come from
  // models instead of arguments passed directly to the view

  var parseSchedule = function(data) {
    // Get the term for the schedule. E.g. Fall 2012
    var termMatch = data.match(/(Spring|Fall|Winter)\s+(\d{4})/);
    var termName;
    if (termMatch) {
      termName = termMatch[0];
    } else {
      throw new Error('Couldn\'t find matching term (Spring|Fall|Winter)');
    }

    // Exact each course item from the schedule
    var titleRe = /(\w{2,5}\ \w{1,5})\ -\ ([^\r\n]+)/g;
    var rawItems = [];
    var match = titleRe.exec(data);
    var lastIndex = -1;
    while (match) {
      if (lastIndex !== -1) {
        var rawItem = data.substring(lastIndex, match.index);
        rawItems.push(rawItem);
      }
      lastIndex = match.index;
      match = titleRe.exec(data);
    }
    if (lastIndex) {
      rawItems.push(data.substring(lastIndex));
    }

    // Process each course item
    var processedItems = [];
    _.each(rawItems, function(rawItem) {
      // Regexes from (with slight changes, i.e. braket on class number):
      // https://github.com/vikstrous/Quest-Schedule-Exporter/blob/master/index.php
      // TODO(Sandy): make this look cleaner (line breaks + comments)
      var bodyRe = /(\d{4})\s+(\d{3})\s+(\w{3})\s+([MThWF]{0,6})\s+([1]{0,1}\d\:[0-5]\d[AP]M)\ -\ ([1]{0,1}\d\:[0-5]\d[AP]M)\s+([\w\ ]+\s+[0-9]{1,5}[A-Z]?)\s+([\w\ \-\,\r\n]+)\s+(\d{2}\/\d{2}\/\d{4})\ -\ (\d{2}\/\d{2}\/\d{4})/g;
      var matches = bodyRe.exec(rawItem);

      if (!matches) {
        return;
      }

      var formatTime = function(timeStr) {
        var result = timeStr;
        // timeStr = '2:20PM'
        var matches = timeStr.match(/(:|PM|AM|\d+)/g);
        // => ['2', ':', '20', 'PM']
        var hours = matches[0];
        var mins = matches[2];
        if (matches[3].toLowerCase() == 'pm' &&
            parseInt(hours, 10) < 12) {
           hours = (parseInt(hours, 10) + 12).toString();
        }
        return hours + ":" + mins;
      };

      // E.g. CS 466 -> cs466
      var courseId = titleRe.exec(data)[1].replace(/\s+/g, '').toLowerCase();
      // E.g. 5300
      var classNum = matches[1];
      // E.g. LEC 001
      var section = matches[2] + " " + matches[3];
      // E.g. TTh -> ['T', 'Th']
      var days = matches[4].match(/[A-Z][a-z]?/g);
      // E.g. 1:00PM
      var startTime = formatTime(matches[5]);
      // E.g. 2:20PM
      var endTime = formatTime(matches[6]);
      // E.g. PHY   313
      var location = matches[7].split(/\s+/g);
      var building = location[0];
      var room = location[1];
      // E.g. Anna Lubiw
      var profName = matches[8];

      var item = {
        course_id: courseId,
        class_num: classNum,
        section: section,
        days: days,
        start_time: startTime,
        end_time: endTime,
        building: building,
        room: room,
        prof_name: profName
      };

      processedItems.push(item);
    });

    return {
      processedItems: processedItems,
      termName: termName
    };
  };

  return {
    ScheduleItem: ScheduleItem,
    ScheduleItemCollection: ScheduleItemCollection,
    ScheduleShareView: ScheduleShareView,
    ScheduleView: ScheduleView,
    ScheduleInputView: ScheduleInputView,
    ScheduleInputModalView: ScheduleInputModalView,
    getPublicScheduleLink: getPublicScheduleLink,
    initScheduleView: initScheduleView,
    parseSchedule: parseSchedule
  };
});
