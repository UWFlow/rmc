/**
 *
 * Delay jobs to make the page remain responsive during expensive jobs.
 *
 * Usage:
 *
 *  require(["work_queue"], function(_work_queue) {
 *    _.each(ids, function(id) {
 *      _work_queue.add(function() {
 *        someExpensiveOperation(id);
 *      });
 *    }):
 *  });
 *
 *  The queue run is started after all events currently queue are processed.
 *
 *  You can pass a second argument to `_work_queue.add` as the `this` context.
 *
 *  var foo = "The Swiftest";
 *  _work_queue.add(function() {
 *    console.log(this);
 *  }, foo);
 *
 */
// TODO(jlfwong): Add async support?
define(['ext/underscore'], function(_) {
  var running = false;
  var queue = [];

  var runNextJob = function() {
    if (queue.length === 0) {
      running = false;
      return;
    }

    var job = queue.shift();

    job.fn.apply(job.context);

    setTimeout(function() {
      runNextJob();
    }, 0);
  };

  var start = function() {
    if (running) {
      return;
    }
    running = true;
    runNextJob();
  };

  return {
    add: function(fn, context) {
      queue.push({
        fn: fn,
        context: context
      });

      setTimeout(start, 0);
    }
  };
});
