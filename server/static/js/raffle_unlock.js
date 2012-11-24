define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap', 'util'],
function(RmcBackbone, $, _, _s, __, util) {

  var RafflePrize = RmcBackbone.Model.extend({
    defaults: {
      id: null,
      name: null,
      points_to_unlock: null
    },

    initialize: function(attributes) {
    }
  });

  var RafflePrizes = RmcBackbone.Collection.extend({
    model: RafflePrize,
    compator: function(rafflePrize) {
      return rafflePrize.get('points_to_unlock');
    }
  });

  var RaffleSupervisor = RmcBackbone.Model.extend({
    defaults: {
      curr_points: null,
      raffle_prizes: null,
      prev_unlock_prize: null,
      next_unlock_prize: null,
      last_unlock_prize: null
    },

    initialize: function(attributes) {
      this.updateUnlockPrizes();
    },

    incrementPoints: function(amount) {
      var currPoints = this.get('curr_points');
      this.set('curr_points', currPoints + amount);
      this.updateUnlockPrizes();
    },

    updateUnlockPrizes: function() {
      var currPoints = this.get('curr_points');
      var rafflePrizes = this.get('raffle_prizes');
      var prevUnlockPrize = null;
      var nextUnlockPrize = null;
      rafflePrizes.every(function(rafflePrize) {
        // We're iterating until we encounter the first raffle prize that
        // requires more points than we currently have to unlock.
        if (currPoints >= rafflePrize.get('points_to_unlock')) {
          prevUnlockPrize = rafflePrize;
          return true;
        }

        nextUnlockPrize = rafflePrize;
        return false;
      }, this);

      this.set('prev_unlock_prize', prevUnlockPrize);
      this.set('next_unlock_prize', nextUnlockPrize);
      this.set('last_unlock_prize', rafflePrizes.last());
    },

    getPrevUnlockPoints: function() {
      var prevUnlockPoints = 0;
      var prevUnlockPrize = this.get('prev_unlock_prize');
      if (prevUnlockPrize) {
        prevUnlockPoints = prevUnlockPrize.get('points_to_unlock');
      }
      return prevUnlockPoints;
    }
  });

  /**
   * A Dropbox spacerace-like bar to show in navbar
   */
  var RaffleUnlockView = RmcBackbone.View.extend({
    MAX_POINTS_RATIO: 1.25,

    template: _.template($('#raffle-unlock-tpl').html()),
    className: 'raffle-unlock',

    initialize: function(attributes) {

      var giftCardPrize = new RafflePrize({
        id: 'card',
        name: '$50 gift card',
        points_to_unlock: 1000
      });

      var dreBeatsPrize = new RafflePrize({
        id: 'dre',
        name: 'Dre beats',
        points_to_unlock: 2000
      });

      var rafflePrizes = new RafflePrizes([
        giftCardPrize,
        dreBeatsPrize
      ]);
      this.raffleSupervisor = new RaffleSupervisor({
        curr_points: 0,
        raffle_prizes: rafflePrizes
      });

      var lastPrize = this.raffleSupervisor.get('last_unlock_prize');
      var lastPrizePoints = lastPrize.get('points_to_unlock');
      this.maxPointsScale = Math.round(lastPrizePoints * this.MAX_POINTS_RATIO);
    },

    render: function() {
      var params = {
        prizes: this.raffleSupervisor.get('raffle_prizes'),
        curr_points: this.raffleSupervisor.get('curr_points'),
        prev_unlock_points: this.raffleSupervisor.getPrevUnlockPoints(),
        next_unlock_prize: this.raffleSupervisor.get('next_unlock_prize'),
        max_points_scale: this.maxPointsScale
      };
      this.$el.html(this.template(params));

      this.$('[rel="tooltip"]').tooltip();

      _.delay(_.bind(this.postRender, this), 500);

      return this;
    },

    postRender: function() {
      var currPoints = this.raffleSupervisor.get('curr_points');
      var prevUnlockPrize = this.raffleSupervisor.get('prev_unlock_prize');

      var completePercent = 0;
      if (prevUnlockPrize) {
        completePercent = 100 * prevUnlockPrize.get(
            'points_to_unlock') / this.maxPointsScale;
      }

      // Always show a little bit of the colored bar
      var totalPercent = Math.max(100 * currPoints / this.maxPointsScale, 1);

      var extraPercents = 2;
      var maxPercentRender = Math.round(100/this.MAX_POINTS_RATIO + extraPercents);

      if (totalPercent > maxPercentRender) {
        totalPercent = maxPercentRender;
      }

      this.$('.bar-incomplete').css({
        width: (totalPercent - completePercent) + '%',
        left: completePercent + '%'
      });
      this.$('.bar').css({
        width: totalPercent + '%'
      });

      this.raffleSupervisor.incrementPoints(600);
      _.delay(_.bind(this.render, this), 5000);
    }
  });


  return {
    RaffleUnlockView: RaffleUnlockView
  };
});
