define(['ext/underscore', 'ext/underscore.string'],
function(_, _s) {

  var NUM_RATINGS_SEGMENTS = 5;

  // From http://stackoverflow.com/a/901144
  var getQueryParam = function(name) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regexS = "[\\?&]" + name + "=([^&#]*)";
    var regex = new RegExp(regexS);
    var results = regex.exec(window.location.search);
    if (results == null) {
      return "";
    } else {
      return decodeURIComponent(results[1].replace(/\+/g, " "));
    }
  };

  /**
   * TODO(mack): check if underscore.string already provides this
   * Capitalize the first letter of a string.
   */
  var capitalize = function(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

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
    if (!_.isString(str) || str.length === 0) return hash;
    for (var i = str.length - 1; i >= 0; --i) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash &= hash;  // Convert to 32-bit integer
    }
    return hash;
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

  return {
    getQueryParam: getQueryParam,
    capitalize: capitalize,
    pluralize: pluralize,
    random: random,
    randomItems: randomItems,
    getDisplayRating: getDisplayRating,
    getHashCode: getHashCode,
    toDate: toDate,
    userCourseTermIdComparator: userCourseTermIdComparator,
    truncatePreviewString: truncatePreviewString,
    getTimeDelta: getTimeDelta,
    getSiteBaseUrl: getSiteBaseUrl
  };
});
