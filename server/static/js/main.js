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

  // TODO((mack): use local copy rather than CDN
  paths: {
    'ext/backbone': 'http://cdnjs.cloudflare.com/ajax/libs/backbone.js/0.9.2/backbone-min',
    'ext/jquery': 'http://cdnjs.cloudflare.com/ajax/libs/jquery/1.8.0/jquery.min',
    'ext/jqueryui': 'http://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.8.23/jquery-ui.min',
    'ext/underscore': 'http://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.3.3/underscore-min',
    'ext/underscore.string': 'http://cdnjs.cloudflare.com/ajax/libs/underscore.string/2.0.0/underscore.string.min',
  }
});

require(['ext/underscore', 'ext/underscore.string'], function(_, _s) {
  // Add helpers functions to all templates
  (function() {
    var template = _.template;

    // TODO(mack): move templateHelpers into own file
    var templateHelpers = {
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
