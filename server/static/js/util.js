define(['ext/underscore', 'ext/underscore.string', 'ext/jquery'],
function(_, _s, $) {

  var getQueryParam = function(name, url) {
    return getQueryParams(url)[name];
  };

  var getQueryParams = function(url) {
    if (!url) {
      url = window.location.search;
    }

    /* jshint -W101 */
    // From: http://stevenbenner.com/2010/03/javascript-regex-trick-parse-a-query-string-into-an-object/
    /* jshint +W101 */
    var queryParams = {};
    var queryStringRE = new RegExp("([^?=&]+)(=([^&]*))?", "g");
    url.replace(queryStringRE, function($0, $1, $2, $3) {
      queryParams[$1] = $3;
    });
    return queryParams;
  };

  /**
   * TODO(mack): check if underscore.string already provides this
   * Capitalize the first letter of a string.
   */
  var capitalize = _s.capitalize;

  /**
   * Return the proper pluralization of num
   */
  var pluralize = function(num, singular, plural) {
    if (num === 1) {
      return singular;
    } else if (typeof plural === 'undefined') {
      return singular + 's';
    } else {
      return plural;
    }
  };

  /**
   * Generate a random integer between in the range [range, to]
   */
  var random = function(from, to) {
    return Math.floor(Math.random() * (to - from + 1) + from);
  };

  /**
   * Generate num random items from an array
   */
  var randomItems = function(items, num) {
    if (num === 0) {
      return [];
    }
    num = Math.min(num, items.length);

    var randItems = _.clone(items);
    var max = randItems.length - 1;
    for (var idx = 0; idx < num; ++idx) {
      var rand = random(idx, max);
      var temp = randItems[idx];
      randItems[idx] = randItems[rand];
      randItems[rand] = temp;
    }

    return _.first(randItems, num);
  };

  var getDisplayRating = function(rating, count, placeholder) {
    if (count !== undefined && count === 0) {
      return placeholder === undefined ? '-' : placeholder;
    }
    return Math.round(rating * 100);
  };

  /**
   * Dumb simple hash code function based on Java's String.hashCode().
   * @param {string} str The string to hash.
   * @return {number} The hash code as an integer.
   */
  var getHashCode = function(str) {
    var hash = 0;
    if (!_.isString(str) || str.length === 0) {
      return hash;
    }
    for (var i = str.length - 1; i >= 0; --i) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash &= hash;  // Convert to 32-bit integer
    }
    return Math.abs(hash);
  };

  /**
   * Get the kitten URL based off the name and number of pictures available
   * @param {string} name The name of the person who the picture is for
   * @return {number} The number for the kitten pic to use
   */
  var getKittenNumFromName = function(name) {
    return getHashCode(name) % pageData.NUM_KITTENS;
  };

  /**
   * Possibly converts a date object we get from json_util into a JS datetime.
   * @param {Object|Date} obj
   * @return {Date}
   */
  var toDate = function(obj) {
    return obj.$date ? new Date(obj.$date) : obj;
  };

  /**
   * Sorts UserCourse objects by term_id ascendingly
   * @param {UserCourse} UserCourse model object
   * @param {UserCourse} UserCourse model object
   * @return {number}
   */
  var userCourseTermIdComparator = function(uc1, uc2) {
    var retVal;
    if (uc1.get('term_id') > uc2.get('term_id')) {
      retVal = 1;
    } else if (uc1.get('term_id') < uc2.get('term_id')) {
      retVal = -1;
    } else {
      retVal = 0;
    }
    return retVal;
  };

  var truncatePreviewString = function(str, n) {
    return str.substr(0, n-1) + (str.length > n ? '&hellip;' : '');
  };

  var getTimeDelta = function(seconds) {
    var days = Math.floor(seconds / 86400);
    seconds -= days * 86400;
    var hours = Math.floor(seconds / 3600);
    seconds -= hours * 3600;
    var minutes = Math.floor(seconds / 60);
    seconds -= minutes * 60;
    return {
      days: days,
      hours: hours,
      minutes: minutes,
      seconds: seconds
    };
  };

  var getSiteBaseUrl = function() {
    // window.location.origin is Webkit only
    if (!window.location.origin) {
      window.location.origin =
          window.location.protocol + "//" + window.location.host;
    }
    return window.location.origin;
  };

  var getReferrerId = function() {
    return getQueryParam('referrer') || getQueryParam('meow');
  };

  var getCurrentUserId = function() {
    return window.pageData.currentUserId ? pageData.currentUserId.$oid : null;
  };

  /**
   * Store a piece of data in localStorage associated with the current user.
   * @param {string} key The key to store the value under. Note that this is
   *     implicitly associated with the current user if one exists.
   * @param {*} value Any JSON-encodable value to store.
   * @param {Date|number} expiration Optional: Date which this key-value should
   *     expire (a call to get will return null/undefined).
   */
  var storeLocalData = function(key, value, expiration) {
    if (!window.localStorage) {
      return;
    }

    var data = { val: value };
    if (expiration) {
      data.exp = +expiration;  // Store timestamp as number
    }
    var userId = getCurrentUserId() || '';
    window.localStorage[userId + '|' + key] = JSON.stringify(data);
  };

  /**
   * Retrieve data from localStorage associated with the current user.
   */
  var getLocalData = function(key) {
    if (!window.localStorage) {
      return;
    }
    var userId = getCurrentUserId() || '';
    var userKey = userId + '|' + key;
    var data = window.localStorage[userKey];

    if (data != null) {
      try {
        data = JSON.parse(data);
      } catch (e) {}
    }

    // Data has expired. Delete it and don't return it.
    if (data && data.exp && +new Date() >= data.exp) {
      delete window.localStorage[userKey];
      return undefined;
    }

    // Handle older formats that were just the unwrapped JSON-encoded value.
    return (_.isObject(data) && 'val' in data) ? data.val : data;
  };

  var scrollToElementId = function(id) {
    // Compensate for nav bar height
    var scrollOffset = $('#course-view-' + id).offset().top;
    var navBarOffset = $('#site-nav').height();

    $('body').animate({
      scrollTop: scrollOffset - navBarOffset,
      duration: 2000
    });
  };

  /**
   * Converts a term ID into a readable form.
   * Eg. "2012_01" => Winter 2012, "2012_05" => "Spring 2012"
   */
  var humanizeTermId = function(termId) {
    var parts = termId.split('_');
    var year = parts[0];
    var month = parseInt(parts[1], 10);
    var season = {
      1: 'Winter',
      5: 'Spring',
      9: 'Fall'
    }[month];

    return season + ' ' + year;
  };

  /**
   * The professor names entered by people when reviewing
   * courses may not precisely match the professor names
   * we have from section information. In order to be able to
   * link the two together, we use the heuristic of taking the
   * first initial and appending the last name.
   *
   * e.g. "Corey Van De Waal" -> "c_waal"
   * e.g. "Larry Smith" -> "l_smith"
   * e.g. "Larry" -> "larry"
   */
  var normalizeProfName = function(profName) {
    var nameParts = profName.split(" ");
    if (nameParts.length >= 2) {
      var firstInitial = nameParts[0].charAt(0).toLowerCase();
      var lastName = nameParts[nameParts.length - 1].toLowerCase();
      return firstInitial + "_" + lastName;
    } else {
      return nameParts[0].toLowerCase();
    }
  };

  /**
   * Converts a professor ID into a readable form.
   * Eg. "byron_weber_becker" => "Byron Weber Becker"
   */
  var humanizeProfId = function(profId) {
    var names = profId.split('_');
    var namesCapitalized = _.map(names, _s.capitalize);
    return namesCapitalized.join(' ');
  };


  /**
   * Converts from an upper-case section type code to a CSS color class.
   */
  // TODO(david): This might be better consolidated elsewhere, but it's 1 am
  //     and I need to ship sections.
  var sectionTypeToCssClass = function(sectionType) {
    var cssClass = {
      LEC: 'blue',
      TUT: 'green',
      LAB: 'red',
      SEM: 'yellow',
      TST: 'orange',
      EXAM: 'orange',  // This is our custom section label for final exams
      PRJ: 'purple'
    }[sectionType];

    return cssClass || 'gray';
  };

  /**
   * Splits a course ID into the department (subject) and course code
   * components.
   * Eg. earth121l => ["EARTH", "121L"]
   */
  var splitCourseId = function(courseId) {
    var matches = /(^[A-z]+)(\w+)/.exec(courseId);
    return [(matches[1] || '').toUpperCase(),
            (matches[2] || '').toUpperCase()];
  };

  /**
   * Converts a course ID into a readable form.
   * Eg. "earth121l" => "EARTH 121L"
   */
  var humanizeCourseId = function(courseId) {
    return splitCourseId(courseId).join(' ');
  };

  /**
   * Convert a term ID from our format to Quest's funky 4-digit code. Eg.
   * 2013_09 => 1139, 2014_01 => 1141.
   */
  var termIdToQuestId = function(termId) {
    var parts = termId.split('_');
    var year = parseInt(parts[0], 10);
    var month = parseInt(parts[1], 10);
    return _s.pad(year - 1900, 3, '0') + month;
  };

  /**
   * Check window size and remove search bar if too small
   */
  var hideSearchIfWindowSmall = function() {
    var size = $(window).width();
    // if size of window is less than 1140px, 
    // the search bar gets push to next line
    // instead, if size goes to less than 1140, search bar is hidden.
    if (size < 1140) {
      $('.unified-search-bar').hide();
    }
    // if search bar was hidden earlier, unhide on window being large enough
    else if (!$('.unified-search-bar').is(":visible")) {
      $('.unified-search-bar').show();
    }
  };

  /**
   * Get term name based on current date.
   */
  var getCurrentTermName = function() {
    var date = new Date();
    var month = date.getMonth();
    var year = date.getFullYear();
    var monthStr = ['Winter', 'Spring', 'Fall'][Math.floor(month/4)];
    return monthStr + ' ' + year;
  };

  return {
    getQueryParam: getQueryParam,
    getQueryParams: getQueryParams,
    capitalize: capitalize,
    pluralize: pluralize,
    random: random,
    randomItems: randomItems,
    getDisplayRating: getDisplayRating,
    getHashCode: getHashCode,
    getKittenNumFromName: getKittenNumFromName,
    toDate: toDate,
    userCourseTermIdComparator: userCourseTermIdComparator,
    truncatePreviewString: truncatePreviewString,
    getTimeDelta: getTimeDelta,
    getSiteBaseUrl: getSiteBaseUrl,
    getReferrerId: getReferrerId,
    storeLocalData: storeLocalData,
    getLocalData: getLocalData,
    scrollToElementId: scrollToElementId,
    humanizeTermId: humanizeTermId,
    humanizeProfId: humanizeProfId,
    normalizeProfName: normalizeProfName,
    sectionTypeToCssClass: sectionTypeToCssClass,
    splitCourseId: splitCourseId,
    humanizeCourseId: humanizeCourseId,
    termIdToQuestId: termIdToQuestId,
    hideSearchIfWindowSmall: hideSearchIfWindowSmall,
    getCurrentTermName: getCurrentTermName
  };
});
