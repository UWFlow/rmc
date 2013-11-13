var page = require('webpage').create();
var system = require('system');

if (system.args.length < 3) {
    console.error("usage: phantom-schedule-screenshot.js schedule_url path/to/output.png");
    phantom.exit(1);
} else {
    var url = system.args[1];
    var outputPath = system.args[2];

    system.stdout.write("Loading " + url + "...\n");
    page.open(url, function() {});
    page.onLoadFinished = function() {
        system.stderr.write("Loaded.\n");
        page.viewportSize = page.evaluate(function(ctx) {
            // TODO(jlfwong): ew ew ew ew ew
            $("#sign-in-banner-container").hide();
            $("#site-nav").hide();
            $("#profile-sidebar").hide();
            $("#site-footer").hide();
            $("#uvTab").hide();
            $("#flDebug").hide();
            $(".schedule-nav").hide();

            var $profileContainer = $("#profile-container");
            var height = $profileContainer.outerHeight();
            // Recommended ratio for photos on facebook is 1.91:1
            // https://developers.facebook.com/docs/opengraph/howtos/maximizing-distribution-media-content/#tags
            var width = 1.91 * height;

            $profileContainer.css({
                width: width,
                position: "absolute",
                padding: 10,
                top: 0,
                left: 0,
                margin: 0
            });

            return {
                width: $profileContainer.outerWidth(),
                height: $profileContainer.outerHeight()
            };
        });

        page.render(outputPath);
        system.stderr.write("Done.\n");
        phantom.exit();
    };
}
