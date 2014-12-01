/* global mochaPhantomJS */
require(['../config_settings'], function(config_settings) {
  var testPaths = config_settings.paths;
  testPaths['ext/chai'] = 'js_tests/vendor/chai';
  testPaths['ext/mocha'] = 'js_tests/vendor/mocha';
  require.config({
    baseUrl: '../',
    paths: testPaths,
    shim: config_settings.shim
  });

  require(['ext/chai', 'ext/mocha'],
      function(chai) {

    /*globals mocha */
    mocha.setup('bdd');

    require([
      'transcript/basic_test.js',
      'schedule/basic_test.js',
      'schedule/different_date_format_test.js',
      'schedule/tba_date_test.js',
      'schedule/prof_name_test.js'
    ], function(require) {
      if (window.mochaPhantomJS) {
        mochaPhantomJS.run();
        mochaPhantomJS.exit();
      } else {
        mocha.run();
      }
    });
  });
});
