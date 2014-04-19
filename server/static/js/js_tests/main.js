// TODO(jeff): Reuse main.js from the main Javascript folder, adding in the
// testing libraries mocha and chai
require.config({
  baseUrl: '../',
  paths: {
    'ext/jquery': 'ext/jquery-1.8.1',
    'ext/underscore': 'ext/underscore-1.3.3',
    'ext/underscore.string': 'ext/underscore.string-2.0.0',
    'moment': 'ext/moment',
    'moment-timezone': 'ext/moment-timezone',
    'mocha': 'js_tests/vendor/mocha',
    'chai': 'js_tests/vendor/chai'
  },
  shim: {
    'ext/underscore': {
      exports: '_'
    },
    'ext/jquery': {
      exports: '$'
    },
    'ext/underscore.string': {
      deps: ['ext/underscore'],
      exports: function(_) {
        return _.string;
      }
    },
    'ext/moment': {
      exports: 'moment'
    }
  }
});

require(['require', 'chai', 'mocha', 'ext/jquery'],
		function(require, chai){

  /*globals mocha */
  mocha.setup('bdd');

  require([
    'transcript_test.js',
    'schedule_test.js'
  ], function(require) {
    mocha.run();
  });

});
