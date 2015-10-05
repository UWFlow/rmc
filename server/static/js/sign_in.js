define(
['ext/jquery', 'ext/underscore', 'ext/bootstrap', 'rmc_backbone', 'facebook',
  'util', 'ext/validate', 'ext/mailcheck'],
function($, _, _bootstrap, RmcBackbone, _facebook, _util, _validate,
  _mailcheck) {

  var emailLoginModalView = null;
  var emailSignUpModalView = null;

  var FbLoginView = RmcBackbone.View.extend({
    className: 'fb-login',

    initialize: function(attributes) {
      this.fbConnectText = attributes.fbConnectText || 'Sign in with Facebook';
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
    hideBannerKey: 'hide-sign-in-banner',
    className: 'sign-in-banner',

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
      // Don't render if the user has previously hidden the banner.
      if (_util.getLocalData(this.hideBannerKey)) {
        return this;
      }

      this.$el.html(this.template({ message: this.message }));
      this.$('.fb-login-placeholder').replaceWith(
        this.fbLoginView.render().el);

      this.$('[title]').tooltip();

      _.defer(_.bind(this.postRender, this));

      return this;
    },

    postRender: function() {
      var $container = this.$el.parent();
      $container.slideDown();
    },

    events: {
      'click .close-banner': 'onCloseBannerClick'
    },

    // TODO(david): Generalize this
    //     "close-button-to-hide-alert-and-save-in-localstorage" pattern as
    //     a mixin or something and re-use for our other annoying alerts (eg.
    //     the "add to shortlist" button).
    onCloseBannerClick: function() {
      this.$el.parent().slideUp('fast');

      // Persist banner close in localstorage for a while.
      _util.storeLocalData(this.hideBannerKey, true,
          /* expiration */ +new Date() + (1000 * 60 * 60 * 24 * 30 * 3));
    }
  });

  var renderBanner = function(attributes) {
    _.defaults(attributes, {
      fbConnectText: 'Sign in with Facebook',
      source: 'UNKNOWN'
    });

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
  var EmailLoginModalView = RmcBackbone.View.extend({
    initialize: function() {
      this.template = _.template($('#email-login-modal-tpl').html());
    },

    events: {
      'submit': 'onSubmit',
      'click .signup-link': 'showSignUpModal'
    },

    render: function() {
      this.$el.html(this.template({}));
      this.$('form').validate({
        rules: {
          email: {
            required: true,
            email: true
          },
          password: 'required'
        },
        messages: {
          email: "Please enter your email address",
          password: "Please enter your password"
        }
      });
      return this;
    },

    onSubmit: function(e) {
      e.preventDefault();

      mixpanel.track('Login: Email login');

      $.ajax('/api/v1/login/email', {
        type: 'POST',
        data: this.$('.login-form').serialize(),
      }).done(function(data) {
        // TODO(sandy): Support nextUrl when we show this modal outside just the
        // front page
        window.location.href = '/profile';
      }).fail(_.bind(displayAjaxError, this, this.$('.errors')));
    },

    showSignUpModal: function(e) {
      var $loginModal = this.$('.email-login-modal');
      var $signupModal = emailSignUpModalView.$('.email-signup-modal');

      $loginModal.modal('hide');
      $loginModal.on('hidden', function() {
        $signupModal.modal('show');
        $loginModal.off('hidden');
      });
    }
  });

  /**
   * Displays errors from a failed AJAX request inside a modal.
   *
   * Expects 'this' to be the modal view.
   *
   * @param $container - The error container JQuery element
   * @param data - Result from the failed AJAX request
   */
  var displayAjaxError = function($container, data) {
    var errorMessage;
    try {
      // Should be an API exception
      errorMessage = $.parseJSON(data.responseText).error;
    } catch (err) {}

    if (!errorMessage) {
      errorMessage = "Something bad happened. Please try again later :(";
    }
    $container
      .html(errorMessage)
      .slideDown();
  };

  var EmailSignUpModalView = RmcBackbone.View.extend({
    initialize: function(attributes) {
      this.template = _.template($('#email-signup-modal-tpl').html());
    },

    events: {
      'submit': 'onSubmit',
      'click .login-link': 'showLoginModal',
      'blur input[name="email"]': 'onEmailInputBlur',
      'click .email-hint': 'onEmailSuggestionClick'
    },

    render: function() {
      this.$el.html(this.template({}));
      this.$('form').validate({
        rules: {
          first_name: {
            required: {
              depends: function(element) {
                return ($('.last-name-input').val().length > 0);
              }
            }
          },
          last_name: {
            required: true
          },
          email: {
            required: true,
            email: true
          },
          password: {
            required: true,
            minlength: 6
          },
          confirm_password: {
            required: true,
            equalTo: '.password-input'
          }
        },
        messages: {
          first_name: "Please enter your name",
          last_name: "Please enter your name",
          email: "Please enter a valid email address",
          password: {
            required: "Please enter a password",
            minlength: "Password must be at least 6 characters long"
          },
          confirm_password: {
            required: "Please re-enter your password",
            equalTo: "Password doesn't match"
          }
        }
      });
      return this;
    },

    // Adapted code from
    // http://andrewberls.com/blog/post/reducing-bad-signup-emails
    // for suggestion
    onEmailInputBlur: function() {
      var $hint = this.$('.email-hint');
      this.$('input[name="email"]').mailcheck({
        suggested: function(element, suggestion) {
          this.$('.email-suggestion').text(
            suggestion.address + '@' + suggestion.domain);
          $hint.fadeIn(50);
        },
        empty: function(element) {
          $hint.fadeOut(50);
        }
      });
    },

    onEmailSuggestionClick: function(e) {
      e.preventDefault();
      var $hint = this.$('.email-hint');
      this.$('input[name="email"]').val(this.$('.email-suggestion').text());
      $hint.fadeOut(50);
    },

    onSubmit: function(e) {
      e.preventDefault();
      var params = this.$('input[name!=confirm_password]').serialize();

      mixpanel.track('Login: Email signup');

      $.ajax('/api/v1/signup/email', {
        type: 'POST',
        data: params
      }).done(function(data) {
        window.location.href = '/profile';
      }).fail(_.bind(displayAjaxError, this, this.$('.errors')));
    },

    showLoginModal: function(e) {
      var $loginModal = emailLoginModalView.$('.email-login-modal');
      var $signupModal = this.$('.email-signup-modal');

      $signupModal.modal('hide');
      $signupModal.on('hidden', function() {
        $loginModal.modal('show');
        $signupModal.off('hidden');
      });
    }
  });

  var renderModal = function(attributes) {
    attributes = _.extend({}, {
      title: 'Please sign in...',
      message: 'Please sign in with Facebook to use this feature.',
      fbConnectText: 'Sign in with Facebook',
      nextUrl: window.location.href
    }, attributes);

    (new SignInModalView(attributes)).show();
  };

  var renderEmailLoginModal = function() {
    if (!emailLoginModalView) {
      emailLoginModalView = new EmailLoginModalView();
      emailLoginModalView.render().$el.appendTo('body');
    }
  };

  var renderEmailSignUpModal = function() {
    if (!emailSignUpModalView) {
      emailSignUpModalView = new EmailSignUpModalView();
      emailSignUpModalView.render().$el.appendTo('body');
    }
  };

  var renderLoginModal = function() {
    emailLoginModalView.$('.email-login-modal').modal('show');
  };

  return {
    renderBanner: renderBanner,
    renderModal: renderModal,
    renderEmailLoginModal: renderEmailLoginModal,
    renderEmailSignUpModal: renderEmailSignUpModal,
    renderLoginModal: renderLoginModal
  };

});
