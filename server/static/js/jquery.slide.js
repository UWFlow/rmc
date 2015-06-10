define(['ext/jquery', 'ext/jqueryui'],
function($, _jqueryui) {

  /**
   * A simple jQuery plugin to be a tiny bit fancier when sliding down (fade in
   * as well).
   */
  $.fn.fancySlide = function(dir, duration, complete) {
    duration = duration === undefined ? 300 : duration;
    complete = complete === undefined ? function() {} : complete;

    if (dir === 'down') {
      return this.css('opacity', 0)
        .animate({
          opacity: 1.0
        }, {
          duration: duration,
          queue: false,
          easing: 'easeOutCubic'
        })
        .slideDown(duration, 'easeOutCubic', complete);
    } else if (dir === 'up') {
      return this.stop(/* clearQueue */ true)
        .slideUp(duration, 'easeOutCubic', complete);
    }

    return this;
  };

});
