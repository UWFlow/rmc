define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap', 'util', 'user'],
function(RmcBackbone, $, _, _s, __, util, _user) {

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
    comparator: function(rafflePrize) {
      return rafflePrize.get('points_to_unlock');
    }
  });

  var RaffleSupervisor = RmcBackbone.Model.extend({
    defaults: {
      total_points: null,
      raffle_prizes: null,
      prev_unlock_prize: null,
      next_unlock_prize: null,
      last_unlock_prize: null
    },

    initialize: function(attributes) {
      this.updateUnlockPrizes();

      // TODO(david): Really weird... this breaks in strange ways
      //this.on('change:total_points', _.bind(this.updateUnlockPrizes, this));

      var currentUser = _user.getCurrentUser();
      if (currentUser) {
        currentUser.on('change:num_points', _.bind(function(model, numPoints) {
          this.incrementPoints(numPoints - model.previous('num_points'));
        }, this));
      }
    },

    incrementPoints: function(amount) {
      var totalPoints = this.get('total_points');
      this.set('total_points', (+totalPoints) + (+amount));
      this.updateUnlockPrizes();
    },

    updateUnlockPrizes: function() {
      var totalPoints = this.get('total_points');
      var rafflePrizes = this.get('raffle_prizes');
      var prevUnlockPrize = null;
      var nextUnlockPrize = null;
      rafflePrizes.every(function(rafflePrize) {
        // We're iterating until we encounter the first raffle prize that
        // requires more points than we currently have to unlock.
        if (totalPoints >= rafflePrize.get('points_to_unlock')) {
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

  // Singleton raffle supervisor
  var raffleSupervisor;
  function getRaffleSupervisor() {
    if (!raffleSupervisor) {
      var giftCardPrize = new RafflePrize({
        id: 'card',
        name: '$50 gift card',
        points_to_unlock: 60000
      });

      var kindlePrize = new RafflePrize({
        id: 'kindle',
        name: 'Kindle',
        points_to_unlock: 125000
      });

      var nexus7Prize = new RafflePrize({
        id: 'nexus-7',
        name: 'Nexus 7',
        points_to_unlock: 200000
      });

      var rafflePrizes = new RafflePrizes([
        giftCardPrize,
        kindlePrize,
        nexus7Prize
      ]);

      raffleSupervisor = new RaffleSupervisor({
        total_points: pageData.totalPoints,
        raffle_prizes: rafflePrizes
      });
    }

    return raffleSupervisor;
  }


  /**
   * A Dropbox spacerace-like bar to show in navbar
   */
  var RaffleUnlockView = RmcBackbone.View.extend({
    MAX_POINTS_RATIO: 1.25,

    className: 'raffle-unlock',

    initialize: function(attributes) {
      this.raffleSupervisor = getRaffleSupervisor();
      this.raffleSupervisor.on(
        'change:total_points', _.bind(this.render, this));

      var lastPrize = this.raffleSupervisor.get('last_unlock_prize');
      var lastPrizePoints = lastPrize.get('points_to_unlock');
      this.maxPointsScale = Math.round(lastPrizePoints * this.MAX_POINTS_RATIO);
      this.template = _.template($('#raffle-unlock-tpl').html());
    },

    render: function() {
      var params = {
        prizes: this.raffleSupervisor.get('raffle_prizes'),
        total_points: this.raffleSupervisor.get('total_points'),
        prev_unlock_points: this.raffleSupervisor.getPrevUnlockPoints(),
        next_unlock_prize: this.raffleSupervisor.get('next_unlock_prize'),
        max_points_scale: this.maxPointsScale
      };
      this.$el.html(this.template(params));

      this.$('[rel="tooltip"]').tooltip();

      this.updateRemainingTime();

      _.delay(_.bind(this.postRender, this), 500);

      return this;
    },

    postRender: function() {
      var totalPoints = this.raffleSupervisor.get('total_points');
      var prevUnlockPrize = this.raffleSupervisor.get('prev_unlock_prize');

      var completePercent = 0;
      if (prevUnlockPrize) {
        completePercent = 100 * prevUnlockPrize.get(
            'points_to_unlock') / this.maxPointsScale;
      }

      // Always show a little bit of the colored bar
      var totalPercent = Math.max(100 * totalPoints / this.maxPointsScale, 1);

      // How much extra colored bar to show past the right-most prize tick
      var extraPercents = 2;
      var maxPercentRender = Math.round(
          100/this.MAX_POINTS_RATIO + extraPercents);

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
    },

    // Update remaining time in raffle periodically
    updateRemainingTime: function() {
      var now = new Date();
      var end = new Date('Wed Dec 12 12:12:12 EST 2012');
      var ended = now >= end;

      if (ended) {
        this.$('.countdown').text('Ended Dec. 12, 2012');
      } else {
        var secondsDelta = Math.floor((end - now) / 1000);
        var timeDelta = util.getTimeDelta(secondsDelta);
        var timeStr = _s.sprintf('%dd %dh %dm %ds',
          timeDelta.days, timeDelta.hours, timeDelta.minutes,
          timeDelta.seconds);
        this.$('.remaining-time').text(timeStr);

        _.delay(_.bind(this.updateRemainingTime, this), 1000);
      }
    }

  });

  return {
    RaffleUnlockView: RaffleUnlockView,
    getRaffleSupervisor: getRaffleSupervisor
  };
});
