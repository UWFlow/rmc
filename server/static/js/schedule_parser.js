define(function(require) {

  var _util = require('util');
  var moment = require('rmc_moment');
  var _ = require('ext/underscore');
  var _s = require('ext/underscore.string');

  var parseSchedule = function(data) {
    // Get the term for the schedule. E.g. Fall 2012
    var termMatch = data.match(/(Spring|Fall|Winter)\s+(\d{4})/);
    var termName;
    if (termMatch) {
      termName = termMatch[0];
    } else {
      termName = _util.getCurrentTermName();
    }

    // TODO(david): Change other places where we assume uppercase to any case
    var ampm = !!(/:\d{2}[AP]M/i.exec(data));

    /* jshint -W101 */
    // Regexes from:
    // https://github.com/vikstrous/Quest-Schedule-Exporter/blob/master/index.php
    // TODO(Sandy): make this look cleaner (line breaks + comments)
    /* jshint +W101 */
    var getTitleRe = function() {
      return (/(\w{2,}\ \w{1,5})\ -\ ([^\r\n]+)/g);
    };

    var getSlotItemRe = function() {
      var wsRe = /\s+/;
      var daysOfWeekRe = /([MThWF]{0,6})/;
      var timeRe = ampm ? /([012]?\d\:[0-5]\d[AP]M)/ : /([012]?\d\:[0-5]\d)/;
      // This can be days of week + time pair, TBA, or empty
      var dayTimePairRe = new RegExp(_s.sprintf('(?:%s%s%s - %s|TBA)?',
          daysOfWeekRe.source, wsRe.source, timeRe.source, timeRe.source));
      // This could be a room, or 'TBA'
      var locationRe = /([\-\w ,]+)/;
      // Apparently, it's possible to have mutiple profs (on separate lines):
      // e.g. Behrad Khamesee,\nJan Huissoon
      var profRe = /([\-\w '.,\r\n]+)/;
      // The day can appear in the following formats:
      // - '01/23/2013'
      // - '23/01/2013'
      // - '2013/01/23'
      // - '2013-01-07'
      /* jshint -W101 */
      var dayRe = /((?:\d{2}\/\d{2}\/\d{4})|(?:\d{4}\/\d{2}\/\d{2})|(?:\d{4}-\d{2}-\d{2}))/;
      /* jshint +W101 */
      var dayPairRe = new RegExp(dayRe.source + ' - ' + dayRe.source);

      var regexStr = [
        dayTimePairRe.source,
        locationRe.source,
        profRe.source,
        dayPairRe.source
      ].join(wsRe.source);

      return new RegExp(regexStr, 'g');
    };

    var getClassItemRe = function() {
      var wsRe = /\s+/;
      // Note: Changed from the github version, added bracket on class number
      var classNumRe = /(\d{4})/;
      var sectionNumRe = /(\d{3})/;
      var sectionTypeRe = /(\w{3})/;
      var slotItemRe = getSlotItemRe();

      var regexStr = [
        classNumRe.source,
        sectionNumRe.source,
        sectionTypeRe.source,
      ].join(wsRe.source);

      // Match one or more slot items
      regexStr = _s.sprintf('%s(?:%s%s)+',
          regexStr, wsRe.source, slotItemRe.source);

      return new RegExp(regexStr, 'g');
    };

    var getCourseRe = function() {
      var regexStr = [
        getTitleRe().source,
        // Match any character
        /[\w\W]+?/.source,
        // Match one or more class items
        _s.sprintf('(?:%s%s)+', /\s+/.source, getClassItemRe().source)
      ].join('');
      return new RegExp(regexStr, 'g');
    };

    // Exact each course item from the schedule
    var rawItems = data.match(getCourseRe());

    var formatTime = function(timeStr) {
      // '2:20PM' => '2:20 PM'
      return timeStr.match(/(AM|PM|\d{1,2}:\d{2})/g).join(' ');
    };

    // Try to find a date format where we're 100% sure of it
    var getDateFormatUsed = function(cNum, sNum, sType, slotItem) {
      var slotMatches = getSlotItemRe().exec(slotItem);

      // The day can appear in the following formats:
      // - '01/23/2013'
      // - '23/01/2013'
      // - '2013/01/23'
      // - '2013-01-07'
      var startDateStr = slotMatches[6];
      var endDateStr = slotMatches[7];

      var dateFormat;
      if (startDateStr.indexOf('-') > -1) {
        dateFormat = 'YYYY-MM-DD';
      } else if ((/\d{4}\/\d{2}\/\d{2}/).exec(startDateStr)) {
        dateFormat = 'YYYY/MM/DD';
      } else {
        // Could be either MM/DD/YYYY or DD/MM/YYYY. It's probably MM/DD/YYYY
        // but if that gives impossible results, we'll assume DD/MM/YYYY
        // instead. See #107.
        var slashRe = /(\d{2})\/(\d{2})\/(\d{4})/;

        var startSlashMatch = slashRe.exec(startDateStr);
        var startMm = parseInt(startSlashMatch[1], 10);
        var startDd = parseInt(startSlashMatch[2], 10);
        var startYyyy = parseInt(startSlashMatch[3], 10);

        var endSlashMatch = slashRe.exec(endDateStr);
        var endMm = parseInt(endSlashMatch[1], 10);
        var endDd = parseInt(endSlashMatch[2], 10);
        var endYyyy = parseInt(endSlashMatch[3], 10);

        // We have a few conditions that we consider 100% accurate
        // We check them in the order of how strong they are
        if (startMm > 12 || endMm > 12 ||
            (startYyyy === endYyyy && startMm > endMm)) {
          // Invalid month or backwards range; this must be DD/MM/YYYY.
          dateFormat = 'DD/MM/YYYY';
        // We use % 4 to check if the month is one of January, May, September
        } else if (endMm - startMm === 3 && startMm % 4 === 1) {
          dateFormat = 'MM/DD/YYYY';
        } else if (endDd - startDd === 3 && startDd % 4 === 1) {
          dateFormat = 'DD/MM/YYYY';
        } else {
          dateFormat = null;
        }
      }
      return dateFormat;
    }

    var processSlotItem = function(cNum, sNum, sType, dateFormat, slotItem) {
      var slotMatches = getSlotItemRe().exec(slotItem);

      // If there's no day-time information, we can't generate schedule items
      if (!slotMatches[1] || !slotMatches[2] || !slotMatches[3]) {
        return [];
      }

      // Grab info from the slot item
      // E.g. TTh -> ['T', 'Th']
      var days = slotMatches[1].match(/[A-Z][a-z]?/g);

      // FIXME(Sandy): Eventually worry about timezones
      // E.g. '2:30PM'
      var startTimeStr = formatTime(slotMatches[2]);
      // E.g. '3:20PM'
      var endTimeStr = formatTime(slotMatches[3]);

      // The day can appear in the following formats:
      // - '01/23/2013'
      // - '23/01/2013'
      // - '2013/01/23'
      // - '2013-01-07'
      var startDateStr = slotMatches[6];
      var endDateStr = slotMatches[7];

      // E.g. PHY   313, TBA
      var location = slotMatches[4].split(/\s+/g);
      var building = location[0];
      // room will be undefined if the location is 'TBA'
      var room = location[1];

      // E.g. Anna Lubiw OR Behrad Khamesee,\nJan Huissoon
      // If more than one prof, only keep the first one
      var profName = slotMatches[5].split(',')[0];

      // Generate each UserScheduleItem
        // TODO(Sandy): Not sure if Saturday's and Sunday's are S and SU
      var weekdayMap = { Su: 0, M: 1, T: 2, W: 3, Th: 4, F: 5, S: 6 };
      var hasClassOnDay = [];
      _.each(days, function(day) {
        hasClassOnDay[weekdayMap[day]] = true;
      });

      var timeFormats = [dateFormat + (ampm ? ' h:mm A' : ' H:mm')];
      var timeZone = "America/Toronto";
      var firstStartMoment = moment.tz(startDateStr + " " + startTimeStr,
          timeFormats, timeZone);
      var firstEndMoment = moment.tz(startDateStr + " " + endTimeStr,
          timeFormats, timeZone);

      // Time delta between start and end time, in milliseconds
      var timeDelta = firstEndMoment - firstStartMoment;

      var processedSlotItems = [];
      // Iterate through all days in the date range
      var currMoment = firstStartMoment;
      var slotEndMoment = moment.tz(endDateStr + " " + startTimeStr,
          timeFormats, timeZone);
      while (currMoment <= slotEndMoment) {
        if (hasClassOnDay[currMoment.day()]) {
          processedSlotItems.push({
            class_num: cNum,
            section_num: sNum,
            section_type: sType,
            start_date: currMoment.unix(),
            end_date: currMoment.unix() + (timeDelta / 1000.0),
            building: building,
            room: room,
            prof_name: profName
          });
        }
        /* jshint -W101 */
        // When this crosses a DST line, it only changes the date, not the time
        //
        //    > moment("2013-11-02 15:00").add('days', 0).tz("America/Toronto").format()
        //    "2013-11-02T18:00:00-04:00"
        //    > moment("2013-11-02 15:00").add('days', 1).tz("America/Toronto").format()
        //    "2013-11-03T18:00:00-05:00"
        //
        /* jshint +W101 */
        currMoment.add('days', 1);
      }
      return processedSlotItems;
    };

    var courses = [];
    var failedCourses = [];
    // Assume a date format, and look for an item where we're 100%
    // certain of the format. Start with a default.
    var dateFormat = 'MM/DD/YYYY';
    var dateFormatSet = false;

    // Process each course item
    _.each(rawItems, function(rawItem) {
      // Grab info from the overall course item
      // E.g. CS 466 -> cs466
      var courseId = getTitleRe().exec(rawItem)[1]
          .replace(/\s+/g, '').toLowerCase();

      // Extract each of the class items
      var classItems = rawItem.match(getClassItemRe());

      if (!classItems.length) {  // No class items extracted.
        failedCourses.push(courseId);
      }

      var course = {
        course_id: courseId,
        items: []
      };
      courses.push(course);

      _.each(classItems, _.bind(function(cId, classItem) {
        var classMatches = getClassItemRe().exec(classItem);

        // Grab the info from the first entry of a class item
        // E.g. 5300
        var classNum = classMatches[1];
        // E.g. 001
        var sectionNum = classMatches[2];
        // E.g. LEC
        var sectionType = classMatches[3];

        // Process each schedule slot of that class item
        var slotItems = classItem.match(getSlotItemRe());

        var getDateFormatUsedBound =
          _.bind(getDateFormatUsed, this, classNum, sectionNum, sectionType)

        if (!dateFormatSet) {
          for (var i = 0; i < slotItems.length; i ++) {
            var possibleDateFormat = getDateFormatUsedBound(slotItems[i]);
            if (possibleDateFormat) {
              // Take the first date format we're sure about, and use that
              dateFormat = possibleDateFormat;
              dateFormatSet = true;
              break;
            }
          }
        }

        var processSlotItemBound =
          _.bind(processSlotItem, this, classNum, sectionNum, sectionType,
              dateFormat);

        var processedSlotItems = _.map(slotItems, processSlotItemBound);

        if (processedSlotItems.length > 0) {
          course.items = course.items.concat(
            // Collapse the list of lists into a list
            _.reduce(processedSlotItems, function(a, b) {
              return a.concat(b);
            })
          );
        }
      }, this, courseId));
    });

    return {
      courses: courses,
      term_name: termName,
      failed_courses: failedCourses
    };
  };

  return {
    parseSchedule: parseSchedule
  };
});
