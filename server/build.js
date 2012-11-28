{
  appDir: 'static/js',
  baseUrl: '.',
  mainConfigFile: 'static/js/main.js',
  dir: 'static/js_prod',

  // Allow nested static dependencies.
  findNestedDependencies: true,

  // Removes uncessary licensing comments
  preserveLicenseComments: false,

  modules: [
    //First set up the common build layer.
    {
      //module names are relative to baseUrl
      name: 'main',
      //List common dependencies here. Only need to list
      //top level dependencies, "include" will find
      //nested dependencies.
      include: [
        'ext/jquery',
        'ext/underscore',
        'ext/backbone'
      ]
    },

    //Now set up a build layer for each main layer, but exclude
    //the common one. "exclude" will exclude nested
    //the nested, built dependencies from "common". Any
    //"exclude" that includes built modules should be
    //listed before the build layer that wants to exclude it.
    //The "page1" and "page2" modules are **not** the targets of
    //the optimization, because shim config is in play, and
    //shimmed dependencies need to maintain their load order.
    //In this example, common.js will hold jquery, so backbone
    //needs to be delayed from loading until common.js finishes.
    //That loading sequence is controlled in page1.js.
    {
      //module names are relative to baseUrl/paths config
      name: 'index_page',
      exclude: ['main']
    },

    {
      name: 'profile_page',
      exclude: ['main']
    },

    {
      name: 'search_page',
      exclude: ['main']
    },

    {
      name: 'course_page',
      exclude: ['main']
    }

  ]
}
