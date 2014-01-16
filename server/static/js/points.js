define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'rmc_backbone', 'util'],
function($, _, _s, bootstrap, RmcBackbone, _util) {

  var Points = RmcBackbone.Model.extend({
    defaults: {
      num_points: 0
    },

    increment: function(points) {
      this.set('points', this.get('points') + points);
    }
  });

  var PointsView = RmcBackbone.View.extend({
    className: 'points-counter',

    initialize: function() {
      this.model.on('change:num_points', _.bind(this.onPointsChange, this));
      this.interval = null;
      this.pointsTicker = this.model.get('num_points');
      this.template = _.template($('#points-counter-tpl').html());
    },

    render: function() {
      this.$el.html(this.template(this.model.toJSON()));

      if (_util.getQueryParam('points')) {
        var $el = this.$el;
        window.setTimeout(function() {
          $el.addClass('highlight');
        }, 1000);
        window.setTimeout(function() {
          $el.removeClass('highlight');
        }, 8000);
      }

      return this;
    },

    onPointsChange: function(model, numPoints, changes) {
      var diff = numPoints - model.previous('num_points');
      if (diff === 0) {
        return;
      }

      // Mario points animation of points earned
      var sign = (diff > 0 ? "+" : "-");
      this.$('.flare').text(sign + diff);

      var $el = this.$el;
      $el.addClass('animated');
      // TODO(david): Use callback when animation is completed
      window.setTimeout(function() {
        $el.removeClass('animated');
      }, 1100);

      // Count up to the desired end value
      if (this.interval) {
        window.clearInterval(this.interval);
      }

      var incrementCounter = _.bind(function() {
        if (this.pointsTicker === numPoints) {
          window.clearInterval(this.interval);
          return;
        }

        var unit = numPoints > this.pointsTicker ? 1 : -1;
        this.pointsTicker += unit;
        this.$('.counter').text(this.pointsTicker + " points");
      }, this);

      this.interval = window.setInterval(incrementCounter, 20);
    }
  });

  // Set up singleton user points model
  var userPoints = new Points({});
  var getUserPoints = function() {
    return userPoints;
  };

  return {
    Points: Points,
    PointsView: PointsView,
    getUserPoints: getUserPoints
  };

});
