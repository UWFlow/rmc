define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'rmc_backbone'],
function($, _, _s, bootstrap, RmcBackbone) {

  var Points = RmcBackbone.Model.extend({
    defaults: {
      num_points: 0
    },

    increment: function(points) {
      this.set('points', this.get('points') + points);
    }
  });

  var PointsView = RmcBackbone.View.extend({
    className: 'points-counter badge',
    template: _.template($('#points-counter-tpl').html()),

    initialize: function() {
      this.model.on('change:num_points', _.bind(this.onPointsChange, this));
    },

    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },

    onPointsChange: function(model, numPoints, changes) {
      this.$el.text(numPoints);
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
