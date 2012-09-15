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

  // TODO((mack): use local copy rather than CDN
  paths: {
    'ext/backbone': 'ext/backbone-0.9.2',
    'ext/jquery': 'ext/jquery-1.8.1',
    'ext/bootstrap': 'ext/bootstrap-2.1.1',
    // TODO(mack): host locally
    'ext/jqueryui': 'http://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.8.23/jquery-ui.min',
    'ext/underscore': 'ext/underscore-1.3.3',
    'ext/underscore.string': 'ext/underscore.string-2.0.0'
  }
});

require(['ext/underscore', 'ext/underscore.string'], function(_, _s) {
  // Add helpers functions to all templates
  (function() {
    var template = _.template;

    // TODO(mack): move templateHelpers into own file
    var templateHelpers = {
      _: _,
      _s: _s,
      fbProfilePicUrl: function(fbid) {
        // TODO(mack): add support for custom width and height
        return _s.sprintf('https://graph.facebook.com/%d/picture', fbid);
      }
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
});
