define (function() {
  var paths = {
    'ext/backbone': 'ext/backbone-0.9.2',
    'ext/jquery': 'ext/jquery-1.8.1',
    'ext/bootstrap': 'ext/bootstrap-2.1.1',
    'ext/select2': 'ext/select2.min',
    'ext/autosize': 'ext/jquery.autosize',
    'ext/cookie': 'ext/jquery.cookie',
    'ext/slimScroll': 'ext/slimScroll-0.6.0',
    'ext/jqueryui': 'ext/jquery-ui-1.8.23.custom.min',
    'ext/toastr': 'ext/toastr',
    'ext/underscore': 'ext/underscore-1.3.3',
    'ext/underscore.string': 'ext/underscore.string-2.0.0',
    'ext/validate': 'ext/jquery.validate.min',
    'ext/smartbanner': 'ext/jquery.smartbanner',
    'ext/mailcheck': 'ext/mailcheck.min',
    'ext/jqueryautocomplete': 'ext/jquery.autocomplete',

    'moment': 'ext/moment',
    'moment-timezone': 'ext/moment-timezone'
  };

  var shim = {
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
    },
    'ext/validate': {
      deps: ['ext/jquery']
    },
    'ext/smartbanner': {
      deps: ['ext/jquery'],
      exports: 'smartbanner'
    },
    'ext/mailcheck': {
      deps: ['ext/jquery']
    },
    'ext/jqueryautocomplete': {
      deps: ['ext/jquery']
    }
  };

  return {
    paths: paths,
    shim: shim
  };
});
