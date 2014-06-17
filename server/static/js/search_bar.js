/*global Bloodhound */

define(['ext/backbone', 'ext/jquery', 'ext/underscore', 'util',
    'ext/typeahead'],
function(RmcBackbone, $, _, _util, _typeahead) {

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
    }
  };

  var itemName = function(item) {
    if (item.type === 'course') {
      return item.label + ' - ' + item.name;
    } else if (item.type === 'friend') {
      return item.label;
    }
  };

  var customSuggestionTemplate = function(item) {
    var formatter;
    if (item.type === 'course') {
      formatter = _.template($('#course-result-item-tpl').html());
      item.department_id = item.department_id.toUpperCase();
    } else if (item.type === 'friend') {
      formatter = _.template($('#friend-result-item-tpl').html());
    }
    return formatter(item);
  };

  var initBloodhoundWithAutocomplete = function(context) {
    var engine = new Bloodhound({
      name: 'friendsAndCourses',
      local: [].concat(_util.getLocalData('friends'),
          _util.getLocalData('courses')),
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
        name: 'friendsAndCourses',
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

  var SearchBarView = RmcBackbone.View.extend({
    initialize: function() {
      this.moving = false;
      this.duration = 300;
      this.baseWidth = 200;
      this.extraWidth = $('.navbar-minus-searchbar').width();
    },

    render: function() {
      var template = _.template($('#search-bar-tpl').html());
      this.$el.html(template);
    },

    events: {
      'focus .search-bar': 'onFocus',
      'blur .search-bar': 'onBlur'
    },

    onFocus: function(event) {
      var self = this;
      if (self.moving) {
        return;
      }
      self.moving = true;
      $(".nav.pull-right").hide(self.duration);
      self.$('.search-div').animate(
        {
          width: (self.baseWidth + self.extraWidth)
        },
        self.duration,
        function() {
          self.$(".search-div").width(self.extraWidth + self.baseWidth);
          self.moving = false;
        }
      );
    },

    onBlur: function(event) {
      var self = this;
      if (self.moving) {
        return;
      }
      self.moving = true;
      $(".nav.pull-right").show(self.duration);
      self.$('.search-div').animate(
        {
          width: self.baseWidth
        },
        self.duration,
        function() {
          self.moving = false;
        }
      );
    },

    getData: function() {
      var self = this;
      var resultTypes = [];
      if (!_util.getLocalData('courses')) {
        resultTypes.push('courses');
      }
      if (!_util.getLocalData('friends')) {
        resultTypes.push('friends');
      }
      resultTypes.join(',');
      if (resultTypes.length > 0) {
        $.ajax({
          dataType: 'json',
          url: '/api/v1/search/bar?result_types=' + resultTypes,
          success: function(data) {
            if (resultTypes.indexOf('courses') >= 0) {
              _util.storeLocalData('courses', data.courses,
                  +(new Date()) + 1000 * 60 * 60 * 24 * 14);
            }
            if (resultTypes.indexOf('friends') >= 0) {
              _util.storeLocalData('friends', data.friends,
                  +(new Date()) + 1000 * 60 * 60 * 24);
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
