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

  // Skews a rating to use our [1.0, 5.0] scale, because that's the range that
  // the user can rate (like ratings with stars)
  var skewRating = function(rating, count) {
    if (count !== undefined && count === 0) {
      return 0;
    }
    return rating * 0.8 + 0.2;
  };

  var getDisplayRating = function(rating, count) {
    if (count !== undefined && count === 0) {
      return '-';
    }
    return _s.sprintf("%.1f", skewRating(rating) * NUM_RATINGS_SEGMENTS);
  };

  /**
   * Dumb simple hash code function based on Java's String.hashCode().
   * @param {string} str The string to hash.
   * @return {number} The hash code as an integer.
   */
  var getHashCode = function(str) {
    var hash = 0;
    if (str.length === 0) return hash;
    for (var i = str.length - 1; i >= 0; --i) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash &= hash;  // Convert to 32-bit integer
    }
    return hash;
  };

  return {
    getQueryParam: getQueryParam,
    capitalize: capitalize,
    pluralize: pluralize,
    random: random,
    randomItems: randomItems,
    skewRating: skewRating,
    getDisplayRating: getDisplayRating,
    getHashCode: getHashCode
  };
});
