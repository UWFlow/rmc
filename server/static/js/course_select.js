define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/select2',
'rmc_backbone', 'course', 'util'],
function($, _, _s, select2, RmcBackbone, course, util) {

// TODO(Sandy): Decide naming. Is CourseSelect good? Maybe CourseSelectBox
  var CourseSelect = RmcBackbone.Model.extend({
    // TODO(Sandy): Allow callback on select
    // Note(Sandy): Not sure if I'm using Backbone right. I have a function here
    // (that isn't needed when rendering the view with .template) and a long
    // list of words that also doesn't get passed to the template. But it's part
    // of this reusable object.
    // TODO(Sandy): Restructure this?
    defaults: {
      placeholderText: "Find a course",
      onSelectHandler: function(event) {},
      // Don't actually have defaults, otherwise we end up loading false data
      /*
      // List of courses to show in the drop down (ordered same as array).
      course_selections: [{
        code: 'SCI 238',
        name: 'Introduction to Astronomy omg omg omg'
      }, {
        code: 'ECON 102',
        name: 'Macro Economics AWESOME COURSE'
      }]
      */
    },

    initialize: function(attributes) {
      if (!attributes || !attributes.course_selections) {
        // TODO(Sandy): Maybe we can strategically fetch this once somewhere
        // before to reduce wait time on first click? Though it looks pretty
        // reasonable now (assuming decent connection)
        if (util.supportsLocalStorage() &&
            window.localStorage.courseSelectData) {
          console.log('nah i got it');
          // XXX(Sandy)[uw]: Allow the server to force clear cache
          // For now, do window.localStorage.remove('courseSelectData')
          this.set('course_selections',
            $.parseJSON(window.localStorage.courseSelectData));
        } else {
          console.log('querying server');
          $.getJSON('/api/courses/codes-names', function(respObj) {
            console.log('code-names ajax return');
            sortedObj = _.sortBy(respObj, function(c) {
              return c.code;
            });

            if (util.supportsLocalStorage()) {
              window.localStorage.courseSelectData = JSON.stringify(sortedObj);
            }
            this.set('course_selections', sortedObj);
          }.bind(this));
        }
      }
    }
  });

  var CourseSelectView = RmcBackbone.View.extend({
    className: 'course-select',
    template: _.template($('#course-select-tpl').html()),

    // XXX(Sandy): WIP
    clearSelection: function() {
      console.log('got cleared');
      console.log(this);
      console.log($(this));
      console.log($(this).find('.course-select'));
      $(this).find('.course-select').select2('val', 'eg.');
      $('.course-select').select2('val', 'eg.');
      console.log('got cleared');
      console.log($('.course-select'));
      console.log($('.course-select').select2('val'));
    },

    render: function() {
      this.$el.html(this.template({
        placeholderText: this.model.get('placeholderText')
      }));

      var courseSelectModel = this.model;
      var queryHandler = function(options) {
        return courseSelectQuery(courseSelectModel, options);
      }

      // Handle the autocomplete course box
      this.$('.course-select-input').select2({
        dropdownCssClass: 'course-select-override-select2',
        formatResult: courseSelectFormatResult,
        formatSelection: courseSelectFormatSelection,
        query: queryHandler
      }).change(this.model.get('onSelectHandler'));

      return this;
    }
  });

  // Internal functions

  var courseSelectFormatResult = function(item) {
    var c = item.course;
    var courseModel = new course.CourseModel({
      code: c.code,
      name: c.name
    });
    // XXX(sandy): make course select not return ratings view
    var courseView = new course.CourseView({
      courseModel: courseModel,
      tagname: 'li'
    });

    var render = courseView.render().$el;
    return render;
  }

  var courseSelectFormatSelection = function(e) {
    // TODO(Sandy): Container content when element selected
    // what does this do again?
    return 'courseSelectFormatSelection';
  }

  var courseSelectQuery = function(courseSelectModel, options) {
    data = {
      results: []
    };

    if (options.context) {
      // Course select data already filtered, just a paging call
      courseSelectData = options.context.filteredCourses;
    } else {
      courseSelectData = courseSelectModel.get('course_selections');

      if (!courseSelectData) {
        // Data fetch might not have finished yet, wait a bit
        console.log('setting timeout to wait for async request');
        setTimeout(function() {
          courseSelectQuery(courseSelectModel, options)
        }, 500);
        return;
      }

      var filterCoursesOnString = function(courses, searchTerm) {
        var keywords = searchTerm.toLowerCase().split(/\s+/);
        var keywordRegExps = new Array();
        _.each(keywords, function(keyword) {
          keywordRegExps.push(new RegExp('\\b' + keyword));
        });

        var courseResults = [];
        _.each(courses, function(c) {
          // XXX(Sandy)[uw]: Give preference to course codes. Eg. "econ" should
          // yield "ECON 101, ECON 102, etc" over "ACTSC 615 - Economics"

          // Filter on the course code (with and without the space) and name
          var str = c.code + " " + c.name + " " + c.code.replace(/\s+/g, '');
          str = str.toLowerCase();

          var match = _.all(keywordRegExps, function(keywordRegExp) {
            return keywordRegExp.test(str);
          });

          if (match) {
            courseResults.push(c);
          }
        });
        return courseResults;
      }

      courseResults = filterCoursesOnString(courseSelectData, options.term)

      data.context = {
        filteredCourses: courseResults
      };
    }

    // Fetch courses for the current page
    // TODO(Sandy): Where do constants go?
    var RESULTS_PER_PAGE = 10;

    var curPage = options.page;
    if (curPage * RESULTS_PER_PAGE < courseResults.length) {
      data.more = true;
    }

    var start = (curPage - 1) * RESULTS_PER_PAGE;
    var end = Math.min(curPage * RESULTS_PER_PAGE, courseResults.length);
    for (var i = start; i < end; ++i) {
      c = courseResults[i];
      // XXX(Sandy): wtf does this do/where is it called/used? removing
      // FormatSelection makes qwe show up...
      data.results.push({
        id: c.code,
        text: 'qwe',
        course: c
      });
    }
    options.callback(data);
    console.log('quer end');
  };

/*
  var selectOnChange = function(event) {
    console.log('selectOnChange');
    console.log(event);
    console.log($('.course-select').select2('val'));
    // USEFUL: This let's you reset the text to the placeholder
    // TODO(Sandy): make this a method of the view
    $('.course-select').select2('val', 'eg.');
  };
  */

  return {
    CourseSelect: CourseSelect,
    CourseSelectView: CourseSelectView
    //CourseSelectCollection: CourseSelectCollection
  };
});
