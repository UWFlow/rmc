/*global Bloodhound */

define(['ext/backbone', 'ext/jquery', 'ext/underscore', 'util',
    'ext/typeahead'],
function(RmcBackbone, $, _, _util, _typeahead) {

  // TODO(david): Move these functions to be direct methods of SearchBarView
  var onOpenedOuter = function(context) {
    return function($e) {
      $('.tt-dropdown-menu').css('width',
          context.baseWidth + context.extraWidth);
    };
  };

  var onSelected = function(event, datum, name) {
    if (datum.type === 'course') {
      window.location.href = '/courses/' + datum.label;
    } else if (datum.type === 'friend') {
      window.location.href = '/profile/' + datum.id;
    } else if (datum.type === 'prof') {
      window.location.href = '/professor/' + datum.prof_id;
    }
  };

  var itemName = function(item) {
    if (item.type === 'course') {
      return _util.humanizeCourseId(item.label) + ' - ' + item.name;
    } else if (item.type === 'friend') {
      return item.label;
    } else if (item.type === 'prof') {
      return item.name;
    }
  };

  var customSuggestionTemplate = function(item) {
    var formatter;
    if (item.type === 'course') {
      formatter = _.template($('#course-result-item-tpl').html());
      item.department_id = item.department_id.toUpperCase();
    } else if (item.type === 'friend') {
      formatter = _.template($('#friend-result-item-tpl').html());
    } else if (item.type === 'prof') {
      formatter = _.template($('#prof-result-item-tpl').html());
      item.kittenNum = _util.getKittenNumFromName(item.name);
    }
    return formatter(item);
  };

  var initBloodhoundWithAutocomplete = function(context) {
    var engine = new Bloodhound({
      name: 'friendsAndCourses',
      local: [].concat(_util.getLocalData('friends'),
          _util.getLocalData('courses', false),
          _util.getLocalData('professors', false)),
      datumTokenizer: function(d) {
        return Bloodhound.tokenizers.whitespace(d.tokens.join(' '));
      },
      queryTokenizer: Bloodhound.tokenizers.whitespace,
      limit: 20
    });
    engine.initialize();
    setUpAutocomplete('.search-bar', engine, context);
  };

  var setUpAutocomplete = function(searchBarElement, engine, context) {
    $(searchBarElement).typeahead(
      {
        hint: true,
        autoselect: true,
        highlight: true,
        minLength: 2,
        limit: 20
      },
      {
        name: 'friendsAndCoursesAndProfessors',
        displayKey: itemName,
        source: engine.ttAdapter(),
        templates: {
          empty: _.template($('#empty-results-message-tpl').html()),
          suggestion: customSuggestionTemplate
        }
      }
    )
    .on('typeahead:opened', onOpenedOuter(context))
    .on('typeahead:selected', onSelected);
  };

  // TODO(david): This search bar collapses when screen is too narrow.
  var SearchBarView = RmcBackbone.View.extend({
    initialize: function() {
      this.duration = 200;
      this.baseWidth = 205;
      this.$navBar = $('.navbar-minus-searchbar');
      this.extraWidth = this.$navBar.width();
    },

    render: function() {
      var template = _.template($('#search-bar-tpl').html());
      this.$el
        .html(template)
        .width(this.baseWidth);
    },

    events: {
      'focus .search-bar': 'onFocus',
      'blur .search-bar': 'onBlur'
    },

    onFocus: function(event) {
      // TODO(david): Investigate the wobble that happens at the end of the
      //     animation. Should use CSS 3 transitions.
      this.$navBar.hide(this.duration);
      this.$el.animate({
        width: this.baseWidth + this.extraWidth
      }, this.duration);
    },

    onBlur: function(event) {
      this.$navBar.show(this.duration);
      this.$el.animate({
        width: this.baseWidth
      }, this.duration);
    },

    getData: function() {
      var self = this;
      var resultTypes = [];
      if (!_util.getLocalData('courses', false)) {
        resultTypes.push('courses');
      }
      if (!_util.getLocalData('friends')) {
        resultTypes.push('friends');
      }
      if (!_util.getLocalData('professors', false)) {
        resultTypes.push('professors');
      }
      resultTypes.join(',');
      if (resultTypes.length > 0) {
        $.ajax({
          dataType: 'json',
          url: '/api/v1/search/unified?result_types=' + resultTypes,
          success: function(data) {
            if (resultTypes.indexOf('courses') >= 0) {
              _util.clearLocalData('|courses');  // Delete old user-bound data
              _util.storeLocalData('courses', data.courses,
                  +(new Date()) + 1000 * 60 * 60 * 24 * 14, false);
            }
            if (resultTypes.indexOf('friends') >= 0) {
              _util.storeLocalData('friends', data.friends,
                  +(new Date()) + 1000 * 60 * 60 * 24);
            }
            if (resultTypes.indexOf('professors') >= 0) {
              _util.clearLocalData('|professors');  // Delete old user-bound data
              _util.storeLocalData('professors', data.professors,
                  +(new Date()) + 1000 * 60 * 60 * 24 * 28, false);
            }
            initBloodhoundWithAutocomplete(self);
          }
        });
      } else {
        initBloodhoundWithAutocomplete(self);
      }
    }
  });

  return {
    SearchBarView: SearchBarView
  };
});
