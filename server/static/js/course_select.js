require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/select2',
'course', 'util'],
function($, _, _s, select2, course, util) {
  // TODO(Sandy): (after rebase) Code here to take into account re-factor that
  // mack did

  // TODO(Sandy): Move this logic to outside this class, to be more generic
  if (util.supportsLocalStorage() && window.localStorage.courseSelectData) {
    // XXX(Sandy)[uw]: Allow the server to force clear cache
    window.pageData.courseSelectData =
      $.parseJSON(window.localStorage.courseSelectData);
  } else {
    $.getJSON('/api/courses/codes-names', function(respObj) {
      console.log('code-names ajax return');
      sortedObj = _.sortBy(respObj, function(c) {
        return c.code;
      });

      if (util.supportsLocalStorage()) {
        window.localStorage.courseSelectData = JSON.stringify(sortedObj);
      }

      window.pageData.courseSelectData = sortedObj;
    });
  }

  var courseSelectFormatResult = function(item) {
    var c = item.course;
    var courseModel = new course.CourseModel({
      code: c.code,
      name: c.name
    });
    var courseView = new course.CourseView({
      courseModel: courseModel,
      tagname: 'li'
    });

    var render = courseView.render().$el;
    return render;
  }

  var courseSelectQuery = function(options) {
    var courseSelectData;
    data = {
      results: []
    };

    if (options.context) {
      // Course select data already filtered, just a paging call
      courseSelectData = options.context.filteredCourses;
    } else {
      courseSelectData = window.pageData.courseSelectData;

      if (!courseSelectData) {
        // Data fetch might not have finished yet, wait a bit
        setTimeout(courseSelectQuery(options), 500);
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
      data.results.push({
        id: c.code,
        text: 'qwe',
        course: c
      });
    }
    options.callback(data);
  };

  var selectOnChange = function(event) {
    console.log('selectOnChange');
    console.log(event);
    console.log($('.course-select').select2('val'));
    $('.course-select').select2('val', 'eg.');
  };

  var couresSelectFormatSelection = function(e) {
    // TODO(Sandy): Container content when element selected
    return 'Add a course';
  }

  // Handle the autocomplete course box
  this.$('#course-select-input').select2({
    dropdownCssClass: 'course-select-override-select2',
    formatResult: courseSelectFormatResult,
    formatSelection: couresSelectFormatSelection,
    query: courseSelectQuery
  }).change(selectOnChange);

});
