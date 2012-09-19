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
    'ext/autosize': 'ext/jquery.autosize-min',
    // TODO(mack): host locally
    'ext/jqueryui': 'http://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.8.23/jquery-ui.min',
    'ext/underscore': 'ext/underscore-1.3.3',
    'ext/underscore.string': 'ext/underscore.string-2.0.0'
  }
});

require(['ext/underscore', 'ext/underscore.string', 'ext/backbone', 'util'], function(_, _s, Backbone, util) {
  // Add helpers functions to all templates
  (function() {
    var template = _.template;

    // TODO(mack): move templateHelpers into own file
    var templateHelpers = {
      _: _,
      _s: _s,
      pluralize: util.pluralize
    };

    _.template = function(templateString, data, settings) {
      if (data) {
        var data = _.extend({}, templateHelpers, data);
        return template(templateString, data, settings);
      } else {
        var compiled = template(templateString);
        return function(data, settings) {
          var data = _.extend({}, templateHelpers, data);
          compiled(data, settings);
        }
      }
    };
  })();

  // Extend backbone model
  // TODO(mack): test in ie
  Backbone.Model.prototype._super = function(funcName) {
    return this.constructor.__super__[funcName].apply(this, _.rest(arguments));
  }
});
