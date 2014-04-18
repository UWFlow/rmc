var page = require('webpage').create();
var system = require('system');

if (system.args.length < 3) {
  console.error(
      "usage: phantom-schedule-screenshot.js schedule_url path/to/output.png");
  phantom.exit(1);
} else {
  var url = system.args[1];
  var outputPath = system.args[2];

  system.stdout.write("Loading " + url + "...\n");
  page.open(url, function() {});

  page.onCallback = function(viewportSize) {
    console.log("Resizing to " + viewportSize.width + "x" +
        viewportSize.height);
    page.viewportSize = viewportSize;
    page.clipRect = {
      top: 0,
      left: 0,
      width: viewportSize.width,
      height: viewportSize.height
    };
    page.render(outputPath);
    system.stderr.write("Done.\n");
    phantom.exit();
  };

  page.onLoadFinished = function() {
    console.log('Loaded.');
    page.evaluate(function() {
      require(["ext/jquery"], function($) {
        var render = function() {
          var scheduleZIndex = 2147483647;
          // Put up a white background to hide everything except for the
          // schedule
          $("<div/>").css({
            width: "100%",
            height: "100%",
            position: "absolute",
            background: "white",
            top: 0,
            left: 0,
            zIndex: scheduleZIndex - 1
          }).appendTo(document.body);

          // Hide the week-changing controls
          $('.schedule-nav .buttons').remove();

          var $profileContainer = $("#profile-container");
          var height = $profileContainer.outerHeight();
          /* jshint -W101 */
          // Recommended ratio for photos on facebook is 1.91:1
          // https://developers.facebook.com/docs/opengraph/howtos/maximizing-distribution-media-content/#tags
          /* jshint +W101 */
          var width = 1.91 * height;

          $profileContainer.css({
            width: width,
            position: "absolute",
            padding: 10,
            top: 0,
            left: 0,
            margin: 0,
            zIndex: scheduleZIndex
          });

          window.callPhantom({
            width: $profileContainer.outerWidth(),
            height: $profileContainer.outerHeight()
          });
        };

        $(document.body).on('pageScriptComplete', render);
        setTimeout(render, 2000);
      });
    });
  };

  setTimeout(function() {
    console.error("Render timeout.");
    phantom.exit(2);
  }, 10000);
}
