define(
['ext/jquery', 'ext/underscore', 'rmc_backbone', 'facebook'],
function($, _, RmcBackbone, _facebook) {

  var FbLoginView = RmcBackbone.View.extend({
    template: _.template($('#fb-login-tpl').html()),

    initialize: function(attributes) {
      this.fbConnectText = attributes.fbConnectText || 'Connect with Facebook';
      this.source = attributes.source;
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
      _facebook.initConnectButton(this.source, window.location.href);
    }
  });

  var SignInBannerView = RmcBackbone.View.extend({
    template: _.template($('#sign-in-banner-tpl').html()),
    attributes: {
      'class': 'sign-in-banner',
      'data-spy': 'affix'
    },

    initialize: function(attributes) {
      this.fbConnectText = attributes.fbConnectText;
      this.fbLoginView = new FbLoginView({
        fbConnectText: this.fbConnectText,
        source: attributes.source
      });
    },

    render: function() {
      this.$el.html(this.template({}));
      this.$('.fb-login-placeholder').replaceWith(
        this.fbLoginView.render().el);

      _.defer(_.bind(this.postRender, this));

      return this;
    },

    postRender: function() {
      // TODO(mack): get affix offset top working (currently just doing in css)
      this.$el.affix();
      var $container = this.$el.parent();
      $container.slideDown();
    }
  });

  var renderBannerIfNecessary = function(source, fbConnectText) {
    if (pageData.currentUserId) {
      return;
    }

    fbConnectText = fbConnectText || 'See what your friends are taking!';
    var signInBannerView = new SignInBannerView({
      fbConnectText: fbConnectText,
      source: source
    });

    $('#sign-in-banner-container')
      // Empty just to be safe...
      .empty()
      .append(signInBannerView.render().$el);
  };

  // TODO(mack): Show loading or something after connecting with facebook,
  // but before redirection completes
  var SignInModalView = RmcBackbone.ModalView.extend({

    template: _.template($('#sign-in-modal-tpl').html()),

    initialize: function(attributes) {
      this.title = attributes.title;
      this.message = attributes.message;
      this.fbLoginView = new FbLoginView({
        fbConnectText: attributes.fbConnectText,
        source: attributes.source
      });
    },

    render: function() {
      this.$el.html(
        this.template({
          title: this.title,
          message: this.message
        })
      );

      // TODO(mack): this causes _facebook.initConnectButton() to execute
      // again,triggering FB.init() which is causes facepile of sign in
      // banner to render again. Maybe should make it not do this
      this.$('.fb-login-placeholder').replaceWith(
        this.fbLoginView.render().el);

      return this;
    }
  });

  var renderModal = function(attributes) {
    attributes = _.extend({}, {
      title: 'Please sign in...',
      message: 'Please connect with Facebook to use this feature.',
      fbConnectText: 'Connect with Facebook'
    }, attributes);

    (new SignInModalView(attributes)).show();
  };

  return {
    renderBannerIfNecessary: renderBannerIfNecessary,
    renderModal: renderModal
  };

});
