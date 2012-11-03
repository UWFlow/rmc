require.config({
  shim: {
    'ext/backbone': {
      deps: ['ext/jquery', 'ext/underscore'],
      exports: 'Backbone'
    },
    // Not really needed since jQuery is already AMD-compliant, but just for
    // the sake of completeness
    'ext/jquery': {
      exports: '$'
    },
    'ext/jqueryui': {
      deps: ['ext/jquery']
    },
    'ext/bootstrap': {
      deps: ['ext/jquery']
    },
    'ext/select2': {
      deps: ['ext/jquery']
    },
    'ext/autosize': {
      deps: ['ext/jquery']
    },
    'ext/cookie': {
      deps: ['ext/jquery']
    },
    'ext/moment': {
      exports: 'moment'
    },
    'ext/slimScroll': {
      deps: ['ext/jquery', 'ext/jqueryui']
    },
    'ext/toastr': {
      deps: ['ext/jquery'],
      exports: 'toastr'
    },
    'ext/underscore': {
      exports: '_'
    },
    'ext/underscore.string': {
      deps: ['ext/underscore'],
      exports: function(_) {
        return _.string;
      }
    }
  },

  baseUrl: '/static/js/',

  paths: {
    'ext/backbone': 'ext/backbone-0.9.2',
    'ext/jquery': 'ext/jquery-1.8.1',
    'ext/bootstrap': 'ext/bootstrap-2.1.1',
    'ext/select2': 'ext/select2.min',
    'ext/autosize': 'ext/jquery.autosize',
    'ext/cookie': 'ext/jquery.cookie',
    'ext/moment': 'ext/moment.min',
    'ext/slimScroll': 'ext/slimScroll-0.6.0',
    'ext/jqueryui': 'ext/jquery-ui-1.8.23.custom.min',
    'ext/toastr': 'ext/toastr',
    'ext/underscore': 'ext/underscore-1.3.3',
    'ext/underscore.string': 'ext/underscore.string-2.0.0',
    'main': 'main.js?v=' + pageData.version
  }
});

require(['ext/jquery', 'ext/underscore', 'ext/underscore.string',
    'ext/backbone', 'util', 'ext/moment', 'ext/bootstrap', 'ext/cookie',
    'ext/toastr'],
function($, _, _s, Backbone, util, moment, __, __, toastr) {
  // Set defaults for toastr notifications
  toastr.options = {
    timeOut: 3000
  };

  (function() {
    // Override bootstrap with saner defaults
    var overrides = {
      animation: false,
      delay: { show: 150 }
    };
    _.extend($.fn.tooltip.defaults, overrides);
    _.extend($.fn.popover.defaults, overrides);
  })();

  // Add helpers functions to all templates
  (function() {
    var template = _.template;

    // TODO(mack): move templateHelpers into own file
    var templateHelpers = {
      _: _,
      _s: _s,
      pluralize: util.pluralize,
      getDisplayRating: util.getDisplayRating,
      moment: moment,
      capitalize: util.capitalize
    };

    _.template = function(templateString, data, settings) {
      templateString = templateString || '';
      if (data) {
        data = _.extend({}, templateHelpers, data);
        return template(templateString, data, settings);
      } else {
        var compiled = template(templateString);
        return function(data, settings) {
          data = _.extend({}, templateHelpers, data);
          return compiled(data, settings);
        };
      }
    };
  })();

  $(function() {
    $('.navbar .signout-btn').tooltip({
      title: 'Sign out',
      placement: 'bottom'
    }).click(function() {
      $.removeCookie('fbid', { path: '/' });
      $.removeCookie('fb_access_token', { path: '/' });
      $.removeCookie('fb_access_token_expires_in', { path: '/' });
      window.location.href = '/?logout=1';
    });
  });

  if (window.pageData.pageScript) {
    // TODO(mack): investigate if there's a faster/better way of doing this
    // than after DOMReady
    $(function() {
      require([window.pageData.pageScript]);
    });
  }

  $(function() {
    // Async-load footer background image
    var $footer = $('footer');
    if ($footer.length && window.location.pathname !== '/') {
      // TODO(david): Use jpg and have it fade out into bg color
      $footer.css('background',
        'url(/static/img/footer_uw_sphere.jpg) left top no-repeat');
    }
  });
});
