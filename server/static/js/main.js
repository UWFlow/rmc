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
    'ext/underscore': {
      exports: '_'
    },
    'ext/underscore.string': {
      deps: ['ext/underscore'],
      exports: function(_) {
        return _.string;
      }
    },
    'ext/facebook': {
      exports: 'FB'
    },
  },

  baseUrl: '/static/js/',

  paths: {
    'ext/backbone': 'ext/backbone-0.9.2',
    'ext/jquery': 'ext/jquery-1.8.1',
    'ext/bootstrap': 'ext/bootstrap-2.1.1',
    'ext/select2': 'ext/select2.min',
    'ext/autosize': 'ext/jquery.autosize-min',
    'ext/cookie': 'ext/jquery.cookie',
    'ext/moment': 'ext/moment.min',
    'ext/slimScroll': 'ext/slimScroll-0.6.0',
    'ext/jqueryui': 'ext/jquery-ui-1.8.23.custom.min',
    'ext/underscore': 'ext/underscore-1.3.3',
    'ext/underscore.string': 'ext/underscore.string-2.0.0',
    // TODO(mack): host locally?
    'ext/facebook': 'http://connect.facebook.net/en_US/all'
  }
});

require(['ext/jquery', 'ext/underscore', 'ext/underscore.string',
    'ext/backbone', 'util', 'ext/moment'],
function($, _, _s, Backbone, util, moment) {
  // Add helpers functions to all templates
  (function() {
    var template = _.template;

    // TODO(mack): move templateHelpers into own file
    var templateHelpers = {
      _: _,
      _s: _s,
      pluralize: util.pluralize,
      getDisplayRating: util.getDisplayRating,
      moment: moment
    };

    _.template = function(templateString, data, settings) {
      if (data) {
        var data = _.extend({}, templateHelpers, data);
        return template(templateString, data, settings);
      } else {
        var compiled = template(templateString);
        return function(data, settings) {
          var data = _.extend({}, templateHelpers, data);
          return compiled(data, settings);
        }
      }
    };
  })();

  // Extend backbone model
  // TODO(mack): test in ie
  Backbone.Model.prototype._super = function(funcName) {
    return this.constructor.__super__[funcName].apply(this, _.rest(arguments));
  };

  if (window.pageData.pageScript) {
    // TODO(mack): investigate if there's a faster/better way of doing this
    // than after DOMReady
    $(function() {

      // Async-load footer background image
      var $footer = $('footer');
      if ($footer.length) {
        // TODO(david): Use jpg and have it fade out into bg color
        $footer.css('background',
          'url(/static/img/footer_background_2000.png) center center no-repeat');
      }
      require([window.pageData.pageScript]);
    });
  }
});
