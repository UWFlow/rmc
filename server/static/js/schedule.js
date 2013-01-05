define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap', 'course', 'util', 'facebook', 'moment'],
function(RmcBackbone, $, _, _s, _bootstrap, _course, _util, _facebook, moment) {

  var minutesSinceSod = function(date) {
    var dateMoment = moment(date);
    return dateMoment.diff(dateMoment.sod(), 'minutes');
  };

  var isSameDay = function(firstDate, secondDate) {
    var firstMoment = moment(firstDate);
    var secondMoment = moment(secondDate);
    return firstMoment.sod().diff(secondMoment.sod()) === 0;
  };

  // TODO(mack): rename UserScheduleItem to match the backend
  var ScheduleItem = RmcBackbone.Model.extend({

    defaults: {
      class_num: '',
      building: '',
      room: '',
      section_type: '',
      section_num: '',
      start_date: '',
      end_date: '',
      course_id: '',
      prof_id: '',
      term_id: ''
    },

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
      return minutesSinceSod(this.get('start_date'));
    },

    endMinutes: function() {
      return minutesSinceSod(this.get('end_date'));
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

    forDay: function(date) {
      var items = new ScheduleItemCollection(this.filter(function(x) {
        return isSameDay(date, x.get('start_date'));
      }));
      items.sort();
      return items;
    }
  });

  ScheduleItemCollection.getSampleScheduleItems = function() {
    return new this([{
      class_num: '1234',
      building: 'DC',
      room: '1350',
      section_type: 'lec',
      section_num: '001',
      start_date: new Date(2013, 0, 2, 12, 30),
      end_date: new Date(2013, 0, 2, 13, 20),
      course_id: 'ece458',
      prof_id: 'bob',
      term_id: '2013_01'
    }, {
      class_num: '1234',
      building: 'DC',
      room: '1350',
      section_type: 'lec',
      section_num: '001',
      start_date: new Date(2013, 0, 4, 12, 30),
      end_date: new Date(2013, 0, 4, 13, 20),
      course_id: 'ece458',
      prof_id: 'bob',
      term_id: '2013_01'
    }, {
      class_num: '1234',
      building: 'DC',
      room: '1350',
      section_type: 'lec',
      section_num: '001',
      start_date: new Date(2013, 0, 8, 12, 30),
      end_date: new Date(2013, 0, 8, 13, 20),
      course_id: 'ece458',
      prof_id: 'bob',
      term_id: '2013_01'
    }
    ]);
  };


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
        .html(this.template({
          item: this.scheduleItem
        }))
        .addClass('well')
        .addClass('truncate');

      return this;
    },

    resize: function(options) {
      this.resizeOptions = options;
      this.margin = 2;

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
        right: rightOffset + this.margin,
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
        'left': -1,
        'right': this.margin
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
      this.date = options.date;
      this.scheduleItems = options.scheduleItems;
      this.scheduleView = options.scheduleView;

      this.itemViews = {};
    },

    render: function() {
      this.$el.html(this.template({
        date: this.date
      }));

      var today = new Date();
      if (isSameDay(this.date, today)) {
        this.$el.addClass('today');
      }

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
      var borderWidth = 1;
      var width = options.width - borderWidth;
      var height = options.height;
      var headerHeight = options.headerHeight;
      var hourHeight = options.hourHeight;

      this.$el.css({
        width: width,
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

        var prevScheduleItem = idx > 0 && this.scheduleItems.at(idx - 1);
        var intersects =
            prevScheduleItem && prevScheduleItem.intersects(currScheduleItem);

        var leftOffset;
        var rightOffset;
        if (intersects) {
          // Deal with conflicts; currently only handles max of 2 intersecting
          // schedule items
          position = (position + 1) % numPositions;
          leftOffset = position/numPositions * width;
          rightOffset = width - ((position + 1) * width/numPositions);
        } else {
          position = 0;
          leftOffset = -1;
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

      if (this.startDate && this.endDate) {
        this.startDate = options.startDate;
        this.endDate = options.endDate;
      } else {
        this.setCurrWeek();
      }

      this.scheduleItems = options.scheduleItems;
      this.resizeOptions = options.resizeOptions;

      this.dayViews = [];
      this.hourLabelViews = [];
    },

    setCurrWeek: function() {
      var currMoment = moment();

      // In out calendar, let us consider saturday to be the start of a week,
      // since people probably aren't interested in classes of the week that
      // just passed
      if (currMoment.day() > 5) {
        currMoment.add('days', 7);
      }

      // The default start and end dates are the Monday and Friday of
      // the current week respectively
      this.startDate = currMoment.day(1).sod().toDate();
      this.endDate = currMoment.day(5).sod().toDate();
    },

    render: function() {
      this.$el.html(this.template({
        schedule: this.schedule,
        start_date: this.startDate,
        end_date: this.endDate
      }));

      // Remove any existing days and hour labels
      while (this.dayViews.length) {
        this.dayViews.shift().close();
      }
      while (this.hourLabelViews.length) {
        this.hourLabelViews.shift().close();
      }

      var $dayContainer = this.$(".day-container");
      // Since moments mutate the underlying date, gotta clone
      var currMoment = moment(new Date(this.startDate));
      var endMoment = moment(this.endDate);
      while (true) {
        if (currMoment.diff(endMoment) > 0) {
          break;
        }

        var itemsForDay = this.scheduleItems.forDay(currMoment.toDate());
        var dayView = new ScheduleDayView({
          date: currMoment.toDate(),
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

        currMoment.add('days', 1);
      }

      var $hourLabelContainer = this.$(".hour-label-container");
      for (var i = this.startHour; i <= this.endHour; i++) {
        var hourLabelView = new ScheduleHourLabelView({
          hour: i
        });
        $hourLabelContainer.append(hourLabelView.render().el);
        this.hourLabelViews.push(hourLabelView);
      }

      if (this.resizeOptions) {
        this.resize(this.resizeOptions);
      }

      return this;
    },

    resize: function(options) {
      this.resizeOptions = options;

      var width = options.width;
      var hourHeight = options.hourHeight;
      var headerHeight = options.headerHeight;
      var hourLabelWidth = options.hourLabelWidth;

      var nHours = this.endHour - this.startHour + 1;
      var height = hourHeight * nHours + headerHeight;

      this.$el.css({
        width: this.width,
        height: this.height
      });

      this.$('.times .header').css({
        height: headerHeight - 2 * headerPadding - headerBorderHeight
      });

      var nDays = moment(this.endDate).diff(moment(this.startDate), 'days') + 1;

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
    },

    events: {
      'click .curr-week-btn': 'changeCurrWeek',
      'click .prev-week-btn': 'changePrevWeek',
      'click .next-week-btn': 'changeNextWeek'
    },

    changeCurrWeek: function(evt) {
      this.setCurrWeek();
      this.changeWeek();
    },

    changePrevWeek: function(evt) {
      this.startDate = moment(this.startDate).subtract('days', 7).toDate();
      this.endDate = moment(this.endDate).subtract('days', 7).toDate();
      this.changeWeek();
    },

    changeNextWeek: function(evt) {
      this.startDate = moment(this.startDate).add('days', 7).toDate();
      this.endDate = moment(this.endDate).add('days', 7).toDate();
      this.changeWeek();
    },

    changeWeek: function(evt) {
      this.render();
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
        return;
      }
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
      scheduleItems: scheduleItems,
      resizeOptions: {
        headerHeight: 30,
        hourHeight: 60,
        hourLabelWidth: 100,
        width: width
      }
    });
    scheduleView.render();

    $(window).resize(function() {
      scheduleView.resize({
        headerHeight: 30,
        height: 800,
        hourLabelWidth: 100,
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

    var extractMatches = function(input, regex) {
      var results = [];
      var match = regex.exec(input);
      var lastIndex = -1;
      while (match) {
        if (lastIndex !== -1) {
          var result = input.substring(lastIndex, match.index);
          results.push(result);
        }
        lastIndex = match.index;
        match = regex.exec(input);
      }
      if (lastIndex) {
        results.push(input.substring(lastIndex));
      }
      return results;
    };

    // Regexes from:
    // https://github.com/vikstrous/Quest-Schedule-Exporter/blob/master/index.php
    // TODO(Sandy): make this look cleaner (line breaks + comments)
    var getTitleRe = function() {
      return (/(\w{2,5}\ \w{1,5})\ -\ ([^\r\n]+)/g);
    };

    var getBodyRe = function() {
      // Note: Changed from the github version, added bracket on class number
      return (/(\d{4})\s+(\d{3})\s+(\w{3})\s+([MThWF]{0,6})\s+([1]{0,1}\d\:[0-5]\d[AP]M)\ -\ ([1]{0,1}\d\:[0-5]\d[AP]M)\s+([\w\ ]+\s+[0-9]{1,5}[A-Z]?)\s+([\w\ \-\,\r\n]+)\s+(\d{2}\/\d{2}\/\d{4})\ -\ (\d{2}\/\d{2}\/\d{4})/g);
    };

    var getPartialBodyRe = function() {
      return (/([MThWF]{0,6})\s+([1]{0,1}\d\:[0-5]\d[AP]M)\ -\ ([1]{0,1}\d\:[0-5]\d[AP]M)\s+([\w\ ]+\s+[0-9]{1,5}[A-Z]?)\s+([\w\ \-\,\r\n]+)\s+(\d{2}\/\d{2}\/\d{4})\ -\ (\d{2}\/\d{2}\/\d{4})/g);
    };

    // Exact each course item from the schedule
    var titleRe = getTitleRe();
    var rawItems = extractMatches(data, titleRe);

    var formatTime = function(timeStr) {
      // '2:20PM' => '2:20 PM'
      return timeStr.match(/(AM|PM|\d{1,2}:\d{2})/g).join(' ');
    };

    var processSlotItem = function(cId, cNum, sNum, sType, slotItem) {
      var slotMatches = getPartialBodyRe().exec(slotItem);

      // Grab info from the slot item
      // E.g. TTh -> ['T', 'Th']
      var days = slotMatches[1].match(/[A-Z][a-z]?/g);

      // FIXME(Sandy): Eventually worry about timezones
      // E.g. '2:30PM'
      var startTimeStr = formatTime(slotMatches[2]);
      // E.g. '3:20PM'
      var endTimeStr = formatTime(slotMatches[3]);

      // E.g. 01/07/2013 (MM/DD/YYYY)
      var startDateStr = slotMatches[6];
      // E.g. 02/15/2013 (MM/DD/YYYY)
      var endDateStr = slotMatches[7];

      // E.g. PHY   313
      var location = slotMatches[4].split(/\s+/g);
      var building = location[0];
      var room = location[1];

      // E.g. Anna Lubiw
      var profName = slotMatches[5];

      // Generate each UserScheduleItem
        // TODO(Sandy): Not sure if Saturday's and Sunday's are S and SU
      var weekdayMap = { Su: 0, M: 1, T: 2, W: 3, Th: 4, F: 5, S: 6 };
      var hasClassOnDay = [];
      _.each(days, function(day) {
        hasClassOnDay[weekdayMap[day]] = true;
      });

      // Time delta between start and end time, in milliseconds
      var timeDelta = moment(startDateStr + " " + endTimeStr) -
          moment(startDateStr + " " + startTimeStr);

      var processedSlotItems = [];
      // Iterate through all days in the date range
      var curDate = moment(startDateStr + " " + startTimeStr);
      var slotEndDate = moment(endDateStr + " " + startTimeStr);
      while (curDate <= slotEndDate) {
        if (hasClassOnDay[curDate.day()]) {
          processedSlotItems.push({
            course_id: cId,
            class_num: cNum,
            section_num: sNum,
            section_type: sType,
            start_date: curDate.unix(),
            end_date: moment(curDate.unix() * 1000 + timeDelta).unix(),
            building: building,
            room: room,
            prof_name: profName
          });
        }
        curDate.add('days', 1);
      }
      return processedSlotItems;
    };

    // Process each course item
    var processedItems = [];
    _.each(rawItems, function(rawItem) {
      // Grab info from the overall course item
      // E.g. CS 466 -> cs466
      var courseId = titleRe.exec(data)[1].replace(/\s+/g, '').toLowerCase();

      var bodyRe = getBodyRe();
      // Extract each of the class items
      var classItems = extractMatches(rawItem, bodyRe);

      _.each(classItems, _.bind(function(cId, classItem) {
        var classMatches = bodyRe.exec(data);
        // Grab the info from the first entry of a class item
        // E.g. 5300
        var classNum = classMatches[1];
        // E.g. 001
        var sectionNum = classMatches[3];
        // E.g. LEC
        var sectionType = classMatches[2];

        // Process each schedule slot of that class item
        var partialBodyRe = getPartialBodyRe();
        var slotItems = classItem.match(partialBodyRe);

        var processSlotItemBound =
          _.bind(processSlotItem, this, cId, classNum, sectionNum, sectionType);

        processedItems = processedItems.concat(
            _.reduce(_.map(slotItems, processSlotItemBound), function(a, b) {
              return a.concat(b);
            })
        );
      }, this, courseId));
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
    initScheduleView: initScheduleView
  };
});
