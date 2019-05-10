define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap', 'user', 'course', 'util', 'facebook',
'rmc_moment', 'schedule_parser'],
function(RmcBackbone, $, _, _s, _bootstrap, _user, _course, _util, _facebook,
  moment, _scheduleParser) {
  // Cache a propery for a given instance.
  var instancePropertyCache = function(getter) {
    return _.memoize(getter, function() {
      return this.cid;
    });
  };
  var minutesSinceSod = function(date) {
    var dateMoment = moment(date);
    return dateMoment.diff(dateMoment.clone().startOf('day'), 'minutes');
  };

  var isSameDay = function(firstDate, secondDate) {
    var firstMoment = moment(firstDate);
    var secondMoment = moment(secondDate);
    return firstMoment.startOf('day').diff(secondMoment.startOf('day')) === 0;
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

    startMinutes: instancePropertyCache(function() {
      return minutesSinceSod(this.get('start_date'));
    }),

    endMinutes: instancePropertyCache(function() {
      return minutesSinceSod(this.get('end_date'));
    })
  });

  var ScheduleItemCollection = RmcBackbone.Collection.extend({
    model: ScheduleItem,

    // This is called _comparator instead of comparator because we don't want
    // Backbone automatically sorting the collection on construction. We avoid
    // this because sorting is an expensive operation due to the moment.tz
    // performance issues. Instead, we only sort use this to sort manually.
    _comparator: function(firstItem, secondItem) {
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
      var DAY_FMT = "YYYY-MM-DD";

      if (!this._forDayCache) {
        this._forDayCache = this.groupBy(function(x) {
          return moment(x.get('start_date')).format(DAY_FMT);
        });
        var comparator = this._comparator;
        _(this._forDayCache).each(function(dayList) {
          dayList.sort(comparator);
        });
      }
      var items = new ScheduleItemCollection(
        this._forDayCache[moment(date).format(DAY_FMT)] || []
      );
      return items;
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
      var sectionType = String(this.scheduleItem.get('section_type'));
      return _util.sectionTypeToCssClass(sectionType);
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
      var height = options.height;
      var headerHeight = options.headerHeight;
      var hourHeight = options.hourHeight;
      var widthPercent = options.widthPercent;

      this.$el.css({
        height: height,
        width: widthPercent + '%'
      });

      var cssHeight = headerHeight - 2 * headerPadding - headerBorderHeight;
      this.$('.header').css({
        height: cssHeight,
        lineHeight: cssHeight + 'px'  // jQuery doesn't px this automatically
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

  var Schedule = RmcBackbone.Model.extend({
    defaults: {
      start_date: null,
      end_date: null,
      schedule_items: null,
      failed_schedule_items: null
    },

    initialize: function() {
      if (!this.get('start_date') || !this.get('end_date')) {
        this.setBestWeek();
      }

      if (this.has('failed_schedule_items')) {
        this.set('courses_not_shown',
          _.chain(this.get('failed_schedule_items'))
            .pluck('course_id')
            .reject(function(courseId) {
              return _s.startsWith(courseId, 'wkrpt');
            })
            .uniq()
            .value()
        );
      }
    },

    setBestWeek: function() {
      var startOfCurrWeek = moment().day(1).startOf('day');

      // Find the closest week in the future with schedule items, or failing
      // that the closest week in the past with schedule items
      var futureItems = this.get('schedule_items').filter(function(item) {
        return startOfCurrWeek <= item.get('start_date');
      });

      if (futureItems.length > 0) {
        futureItems = _(futureItems).sortBy(function(item) {
          return moment(item.get('start_date')).unix();
        });
        this.setWeek(moment(futureItems[0].get('start_date')).clone().day(1)
            .startOf('day').toDate());
      } else {
        var pastItems = this.get('schedule_items').filter(function(item) {
          return startOfCurrWeek.unix() > moment(item.get('start_date')).unix();
        });
        pastItems = _(pastItems).sortBy(function(item) {
          return moment(item.get('start_date')).unix();
        });
        this.setWeek(moment(pastItems[pastItems.length-1].get('start_date'))
            .clone().day(1).startOf('day').toDate());
      }
    },

    setWeek: function(startDate) {
      startDate = moment(startDate).day('Monday');

      // Check if there's events on the 6th and 7th days to display weekend
      var sixthDay = startDate.clone().add('days', 5).toDate();
      var seventhDay = startDate.clone().add('days', 6).toDate();
      var endDate = null;
      if (!this.get('schedule_items').forDay(sixthDay).isEmpty() ||
          !this.get('schedule_items').forDay(seventhDay).isEmpty()) {
        endDate = seventhDay;
      } else {
        endDate = moment(startDate).clone().add('days', 4).toDate();
      }

      this.set({ start_date: startDate, end_date: endDate });
    },

    setCurrWeek: function() {
      var currMoment = moment();

      // Start the week on the Monday of the current week
      this.setWeek(currMoment.day(1).startOf('day').toDate());
    },

    setNextWeek: function() {
      this.setWeek(
          moment(this.get('start_date')).clone().add('days', 7).toDate());
    },

    setPrevWeek: function() {
      this.setWeek(
          moment(this.get('start_date')).clone().subtract('days', 7).toDate());
    }
  });

  var ScheduleView = RmcBackbone.View.extend({
    template: _.template($("#schedule-tpl").html()),

    className: 'class-schedule',

    initialize: function(options) {
      this.startHour = options.maxStartHour;
      this.endHour = options.minEndHour;

      this.schedule = options.schedule;
      this.schedule.on('change:start_date change:end_date', this.render, this);

      this.scheduleItems = options.scheduleItems;
      this.resizeOptions = options.resizeOptions;

      this.showSharing = options.showSharing;
      if (this.showSharing) {
        this.scheduleShareView = new ScheduleShareView({
          schedule: this.schedule
        });
      }

      this.dayViews = [];
      this.hourLabelViews = [];
    },

    render: function() {
      this.$el.html(this.template({
        start_date: this.schedule.get('start_date'),
        end_date: this.schedule.get('end_date'),
        total_hours: this.calculateHoursPerWeek(this.schedule),

        // TODO(david): Only show for appropriate term
        courses_not_shown: this.schedule.get('courses_not_shown')
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
      var currMoment = moment(this.schedule.get('start_date')).clone();
      var endMoment = moment(this.schedule.get('end_date'));
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

      if (this.scheduleShareView) {
        this.$('.schedule-share-placeholder').replaceWith(
            this.scheduleShareView.render().el);
        this.scheduleShareView.delegateEvents();
      }

      return this;
    },

    calculateHoursPerWeek: function(schedule) {
      var curDay = moment(schedule.get('start_date'));
      var endDay = moment(schedule.get('end_date'));
      var hours = 0;

      // Get all schedule items for the week
      while (!curDay.isAfter(endDay)) {
        var scheduleItems = schedule.get('schedule_items').forDay(curDay);
        scheduleItems.each(function(curScheduleItem) {
          var endMinute = curScheduleItem.endMinutes();
          var startMinute = curScheduleItem.startMinutes();

          var curHours = (endMinute - startMinute) / 60;
          hours += curHours;
        });
        curDay = moment(curDay.clone().add('days', 1).toDate());
      }

      hours = Math.round(hours);
      return hours;
    },

    resize: function(options) {
      this.resizeOptions = options;

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

      var nDays = moment(this.schedule.get('end_date')).diff(
          moment(this.schedule.get('start_date')), 'days') + 1;

      _.each(this.dayViews, function(dayView) {
        dayView.resize({
          height: height,
          headerHeight: headerHeight,
          hourHeight: hourHeight,
          widthPercent: 100/nDays
        });
      });

      _.each(this.hourLabelViews, function(hourLabelView) {
        hourLabelView.resize({height: hourHeight});
      });

      return this;
    },

    events: {
      'click .curr-week-btn': 'onChangeCurrWeek',
      'click .prev-week-btn': 'onChangePrevWeek',
      'click .next-week-btn': 'onChangeNextWeek'
    },

    onChangeCurrWeek: function(evt) {
      this.schedule.setCurrWeek();
    },

    onChangePrevWeek: function(evt) {
      this.schedule.setPrevWeek();
    },

    onChangeNextWeek: function(evt) {
      this.schedule.setNextWeek();
    }
  });

  var ScheduleInputView = RmcBackbone.View.extend({
    template: _.template($('#schedule-input-tpl').html()),

    className: 'schedule-input',

    events: {
      'input .schedule-input-textarea': 'inputSchedule',
      'click .schedule-input-textarea': 'onFocus'
    },

    initialize: function() {
    },

    render: function() {
      this.$el.html(this.template({}));
      return this;
    },

    onFocus: function() {
      this.$('.schedule-input-textarea').select();
    },

    inputSchedule: function(evt) {
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
      var exceptionThrown = false;
      try {
        scheduleData = _scheduleParser.parseSchedule(data);
        this.$('.schedule-input-textarea').prop('disabled', true);
      } catch (ex) {
        mixpanel.track('Schedule parse error', { error_msg: ex.toString() });
        exceptionThrown = true;
      }

      if (exceptionThrown || !scheduleData.courses.length) {
        $.ajax('/api/schedule/log', {
          data: {
            schedule: data
          },
          type: 'POST'
        });

        window.alert(
          'Uh oh, we couldn\'t parse your schedule. ' +
          'Please make sure you copied the List View (not the Weekly ' +
          'Calendar View) and try again.\n\n' +
          'If that still doesn\'t work, click the "Feedback" button ' +
          'on the left to let us know.'
        );

        this.$('.schedule-input-textarea').prop('disabled', false);
        this.onFocus();
        return;
      }

      var missingInfoCourses = _.reduce(scheduleData.courses,
        function(courses, course) {
          if (!course.items.length) {
            courses.push(course.course_id);
          }
          return courses;
        }, []);
      if (scheduleData.failed_courses.length || missingInfoCourses.length) {
        var failedCourses = _.map(
          _.union(scheduleData.failed_courses, missingInfoCourses),
          function(courseId) {
            return courseId.toUpperCase();
          }
        );

        window.alert(
          'Uh oh, it seems like ' + failedCourses.join(', ') +
          _util.pluralize(failedCourses.length, ' is ', ' are ') +
          'missing details (maybe meeting times are "To Be Announced"), ' +
          'so we can\'t show ' +
          _util.pluralize(failedCourses.length, 'it ', 'them ') +
          'on your schedule.\n\n' +
          'You can reimport when details are available.\n\n' +
          'If details are not missing, click the "Feedback" button ' +
          'on the left to let us know.'
        );
      }

      this.$('.schedule-input-textarea').addClass('schedule-input-loader');
      _gaq.push([
        '_trackEvent',
        'USER_GENERIC',
        'SCHEDULE_UPLOAD'
      ]);
      mixpanel.track('Schedule uploaded');
      $.post(
        '/api/schedule', {
          'schedule_text': data,
          'schedule_data': JSON.stringify(scheduleData)
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
      // Set a tabIndex so that it can have focus, and thus be dismissed by esc
      this.$('.schedule-input-modal').prop('tabIndex', '0');
      return this;
    }
  });

  var ScheduleShareView = RmcBackbone.View.extend({
    template: _.template($('#schedule-share-tpl').html()),

    className: 'schedule-share',

    initialize: function(options) {
      if (options.schedule) {
        this.schedule = options.schedule;
        this.schedule.on('change:start_date', this.render, this);
      }
    },

    events: {
      'click .facebook-btn': 'shareScheduleFacebook',
      'click .link-box': 'onFocus',
      'click .reimport-btn': 'openImportModal',
      'click .google-calendar-export-btn': 'logGoogleCalendarExport',
      'click .icalendar-export-btn': 'logICalendarExport'
      // TODO(Sandy): Restore text after clicking away?
    },

    openImportModal: function() {
      $('.schedule-input-modal').modal();
    },

    onFocus: function() {
      this.$('.link-box').select();
      this.logShareIntent('Link box');
    },

    _getScheduleShareUrl: function() {
      return (getPublicScheduleLink() + '?start_date=' +
          Number(this.schedule.get('start_date')));
    },

    shareScheduleFacebook: function() {
      var self = this;

      var profileUser = _user.UserCollection.getFromCache(
          pageData.profileUserId.$oid);
      $.getJSON("/api/schedule/screenshot_url", function(data) {
        if (!data.url) {
          mixpanel.track('Schedule Screenshot Not Ready');
        }
        _facebook.showFeedDialog({
          link: self._getScheduleShareUrl(),
          name: profileUser.get('first_name') + "'s Class Schedule",
          description: 'Flow is a social course planning app for Waterloo' +
              ' students.',
          // TODO(jlfwong): What picture should we use if the schedule
          // screenshot isn't ready?
          picture: data.url,
          callback: function() {
            self.logShareCompleted('Facebook');
          }
        });
      });
      self.logShareIntent('Facebook');
    },

    logGoogleCalendarExport: function() {
      mixpanel.track('Schedule Export', {
        ExportType: 'Google Calendar'
      });
    },

    logICalendarExport: function() {
      mixpanel.track('Schedule Export', {
        ExportType: 'iCalendar'
      });
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
      var scheduleUrl = this._getScheduleShareUrl();
      var iCalUrl = getICalScheduleUrl();
      var printUrl = scheduleUrl + '&print=1';

      this.$el.html(this.template({
        url: scheduleUrl,
        iCalUrl: iCalUrl,
        printUrl: printUrl
      }));

      this.$('.reimport-btn')
        .tooltip({
          title: 'Reimport your schedule from Quest',
          placement: 'bottom',
          animation: false
        });
      return this;
    }
  });

  var initScheduleView = function(options) {
    var width = options.width;
    var scheduleItems = options.scheduleItems;

    var schedule = options.schedule || new Schedule({
      schedule_items: scheduleItems,
      failed_schedule_items: options.failedScheduleItems
    });
    var scheduleView = new ScheduleView({
      schedule: schedule,
      maxStartHour: 8,
      minEndHour: 18,
      scheduleItems: scheduleItems,
      showSharing: options.showSharing,
      resizeOptions: {
        headerHeight: 25,
        hourHeight: 46,
        width: width
      }
    });
    scheduleView.render();

    return scheduleView;
  };

  var getPublicScheduleLink = function() {
    return _util.getSiteBaseUrl() +
        '/schedule/' + window.pageData.profileUserSecretId;
  };

  var getICalScheduleUrl = function() {
    var baseURL = _util.getSiteBaseUrl().replace('https', 'webcal');
    var d = new Date();

    return baseURL +
        '/schedule/ical/' + window.pageData.profileUserSecretId +
        '.ics?noCache=' + d.getTime();
  };

  return {
    ScheduleItem: ScheduleItem,
    ScheduleItemCollection: ScheduleItemCollection,
    ScheduleShareView: ScheduleShareView,
    Schedule: Schedule,
    ScheduleView: ScheduleView,
    ScheduleInputView: ScheduleInputView,
    ScheduleInputModalView: ScheduleInputModalView,
    getPublicScheduleLink: getPublicScheduleLink,
    initScheduleView: initScheduleView
  };
});
