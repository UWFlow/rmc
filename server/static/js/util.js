define([],
function() {
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

  return {
    getQueryParam: getQueryParam,
    capitalize: capitalize,
    pluralize: pluralize
  };
});
