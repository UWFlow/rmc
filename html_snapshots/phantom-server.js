/* global require, phantom, $ */

var page = require('webpage').create();
var system = require('system');

/**
 * Based off: https://github.com/ariya/phantomjs/blob/master/examples/waitfor.js
 *
 * Wait until the test condition is true or a timeout occurs. Useful for waiting
 * on a server response or for a ui change (fadeIn, etc.) to occur.
 */
function waitFor(condition, onReady, timeOutMillis) {
  timeOutMillis = timeOutMillis || 3000;
  var startTime = (new Date()).getTime();

  (function checkCondition() {
    if (condition()) {
      onReady();
      phantom.exit(0);
      return;
    }
    var elapsedTime = (new Date()).getTime() - startTime;
    if (elapsedTime > timeOutMillis) {
      // TODO(mack): log to stderr
      console.log("'waitFor()' timeout");
      phantom.exit(1);
      return;
    }
    setTimeout(checkCondition, 250);
  })();
}

var url = system.args[1];
page.open(url, function() {});
page.onLoadFinished = function() {
  // TODO(mack): Find place to log to other than stdout since that is used for
  // communication; then re-enable
  //page.onConsoleMessage = function() {
  //  var args = [].slice.apply(arguments);
  //  args.unshift('Log:');
  //  console.log.apply(console, args);
  //};

  waitFor(
    function() {
      return page.evaluate(function() {
        return typeof jQuery !== 'undefined' &&
          !!$(document.body).data('rendered');
      });
    },
    function() {
      page.evaluate(function() {
        $('script').remove();
      });
      var html = page.content;
      console.log(html);
      phantom.exit();
    },
    10000
  );
};

// See: http://stackoverflow.com/questions/22274112
page.onResourceRequested = function(requestData, request) {
  if ((/google-analytics\.com/gi).test(requestData['url'])){
    request.abort();
  }
};
