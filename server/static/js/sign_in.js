define(
['ext/jquery', 'ext/underscore', 'rmc_backbone', 'facebook'],
function($, _, RmcBackbone, _facebook) {

  var FbLoginView = RmcBackbone.View.extend({

    initialize: function(attributes) {
      this.fbConnectText = attributes.fbConnectText || 'Connect with Facebook';
      this.source = attributes.source;
      this.nextUrl = attributes.nextUrl;
      this.template = _.template($('#fb-login-tpl').html());
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
      // If facebook is already initialized, gotta reinitialize to render the
      // facepile that was just added to the page
      if (_facebook.initializedFacebook()) {
        _facebook.initFacebook(true);
      }

      _facebook.initConnectButton({
        source: this.source,
        nextUrl: this.nextUrl
      });
    }
  });

  var SignInBannerView = RmcBackbone.View.extend({
    className: 'sign-in-banner',

    attributes: {
      'data-spy': 'affix'
    },

    initialize: function(options) {
      this.fbLoginView = new FbLoginView({
        fbConnectText: options.fbConnectText,
        source: options.source,
        nextUrl: options.nextUrl
      });
      this.message = options.message || '';
      this.template = _.template($('#sign-in-banner-tpl').html());
    },

    render: function() {
      this.$el.html(this.template({ message: this.message }));
      this.$('.fb-login-placeholder').replaceWith(
        this.fbLoginView.render().el);

      $('#sign-in-banner-container')
          .toggleClass('with-message', !!this.message);

      _.defer(_.bind(this.postRender, this));

      return this;
    },

    postRender: function() {
      var $container = this.$el.parent();
      $container.slideDown();
    }
  });

  var renderBanner = function(attributes) {
    attributes = _.extend({}, {
      fbConnectText: 'Connect with Facebook',
      source: 'UNKNOWN'
    }, attributes);

    var signInBannerView = new SignInBannerView(attributes);

    $('#sign-in-banner-container')
      // Empty just to be safe...
      .empty()
      .append(signInBannerView.render().$el);
  };

  // TODO(mack): Show loading or something after connecting with facebook,
  // but before redirection completes
  // TODO(david): Remove RmcBackbone.ModalView (just use Bootstrap's JS)
  var SignInModalView = RmcBackbone.ModalView.extend({

    initialize: function(attributes) {
      this.title = attributes.title;
      this.message = attributes.message;
      this.fbLoginView = new FbLoginView({
        fbConnectText: attributes.fbConnectText,
        source: attributes.source,
        nextUrl: attributes.nextUrl
      });
      this.template = _.template($('#sign-in-modal-tpl').html());
    },

    render: function() {
      this.$el.html(
        this.template({
          title: this.title,
          message: this.message
        })
      );

      this.$('.fb-login-placeholder').replaceWith(
        this.fbLoginView.render().el);

      return this;
    }
  });

  // TODO(david): Consolidate this w/ other code. Gotta rush this out right now.
  var EmailSignInModalView = RmcBackbone.View.extend({
    initialize: function() {
      this.template = _.template($('#email-sign-in-modal-tpl').html());
    },

    render: function() {
      this.$el.html(this.template({}));
      return this;
    },

    events: {
      'click .send-email-btn': 'onSendEmailBtnClick',
      'keypress .email-input': 'onEmailInputKeypress'
    },

    onSendEmailBtnClick: function() {
      this.saveEmail();
    },

    onEmailInputKeypress: function(evt) {
      if (evt.keyCode === 13 /* enter key */) {
        this.saveEmail();
      }
    },

    saveEmail: function() {
      var email = this.$('.email-input').val();
      $.post('/api/sign_up_email', { email: email });
      this.$('.submit-msg').fadeIn();
    }
  });

  var renderModal = function(attributes) {
    attributes = _.extend({}, {
      title: 'Please sign in...',
      message: 'Please connect with Facebook to use this feature.',
      fbConnectText: 'Connect with Facebook',
      nextUrl: window.location.href
    }, attributes);

    (new SignInModalView(attributes)).show();
  };

  var renderEmailSignInModal = function() {
    var emailSignInModalView = new EmailSignInModalView();
    emailSignInModalView.render().$el.appendTo('body');
  };

  return {
    renderBanner: renderBanner,
    renderModal: renderModal,
    renderEmailSignInModal: renderEmailSignInModal
  };

});
