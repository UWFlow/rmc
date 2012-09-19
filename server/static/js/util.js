define(['ext/underscore'],
function(_) {

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
    } else if (num >= items.length) {
      return _.clone(items);
    }

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

  return {
    getQueryParam: getQueryParam,
    capitalize: capitalize,
    pluralize: pluralize,
    random: random,
    randomItems: randomItems
  };
});
