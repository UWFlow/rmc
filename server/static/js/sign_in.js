define(
['ext/jquery', 'ext/underscore', 'rmc_backbone', 'facebook'],
function($, _, RmcBackbone, _facebook) {

  var SignInBannerView = RmcBackbone.View.extend({
    template: _.template($('#sign-in-banner-tpl').html()),
    attributes: {
      'class': 'sign-in-banner',
      'data-spy': 'affix'
    },

    initialize: function(attributes) {
      $(window).scroll(_.bind(this.scrollWindow, this));
      this.fbConnectText = attributes.fbConnectText;
    },

    scrollWindow: function(evt) {
    },

    render: function() {
      this.$el.html(
        this.template({
          fb_connect_text: this.fbConnectText
        })
      );
      _.defer(_.bind(this.postRender, this));

      return this;
    },

    postRender: function() {
      // TODO(mack): get affix offset top working (currently just doing in css)
      this.$el.affix();

      _facebook.initConnectButton(window.location.href);

      // Delay when the banner shows so that facebook has time to first load
      // the facepile
      // TODO(mack): Might need to make delay longer so that animation is
      // better
      // TODO(mack): There's a bug with the banner being shown as hovered on
      // when we are underneath it (since facepile has height > banner)
      var $container = this.$el.parent();
      window.setTimeout(function() {
        $container.slideDown();
      }, 1000);
    }
  });

  var renderBannerIfNecessary = function(fbConnectText) {
    if (pageData.currentUserId) {
      return;
    }

    fbConnectText = fbConnectText || 'See what your friends are taking!';
    var signInBannerView = new SignInBannerView({
      fbConnectText: fbConnectText
    });

    $('#sign-in-banner-container')
      // Empty just to be safe...
      .empty()
      .append(signInBannerView.render().$el);
  };

  return {
    renderBannerIfNecessary: renderBannerIfNecessary
  };

});
