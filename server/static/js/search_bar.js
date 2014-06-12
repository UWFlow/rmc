/*global Bloodhound */

define(['ext/backbone', 'ext/jquery', 'ext/underscore', 'util',
    'ext/typeahead'],
function(RmcBackbone, $, _, _util, _typeahead) {

  var SearchBarView = RmcBackbone.View.extend({
    initialize: function() {
      this.moving = false;
      this.duration = 300;
      this.baseWidth = 200;
      this.extraWidth = $('ul.pull-right').width();
    },

    render: function() {
      var template = _.template($('#search-bar-tpl').html());
      this.$el.html(template);
    },

    events: {
      'focus .search-bar': 'onFocus',
      'blur .search-bar': 'onBlur'
    },

    onFocus: function(event){
      var self = this;
      $('.search-div').css('opacity', 1.0);
      if (self.moving) {
        return;
      } else {
        self.moving = true;
      }
      $('.twitter-typeahead').animate({
        width: (self.baseWidth + self.extraWidth)
      },
      self.duration,
      function() {
        $(".twitter-typeahead").width(self.extraWidth + self.baseWidth);
        self.moving = false;
      }
      );
      $(".nav.pull-right").hide(self.duration);
      $('.search-div').animate({
        width: (self.baseWidth + self.extraWidth)
      },
      self.duration,
      function() {
        $(".search-div").width(self.extraWidth + self.baseWidth);
        self.moving = false;
      }
      );
    },

    onBlur: function(event){
      var self = this;
      $('.search-div').css('opacity', 0.8);
      if (self.moving) {
        return;
      } else {
        self.moving = true;
      }
      $('.twitter-typeahead').animate({
        width: self.baseWidth
      },
      self.duration
      );
      $(".nav.pull-right").show(self.duration);
      $('.search-div').animate({
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

      var onOpened = function($e) {
        $('.tt-dropdown-menu').css('width', self.baseWidth + self.extraWidth);
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
          console.log(item.program);
          if (item.program == null) {
            // We need this so the spacing isn't messed up on the suggestions
            item.program = "&nbsp;";
          }
          formatter = _.template($('#friend-result-item-tpl').html());
        }
        return formatter(item);
      };

      var engine;

      var initBloodhoundWithAutocomplete = function() {
        engine = new Bloodhound({
          name: 'friendsAndCourses',
          local: [].concat(_util.getLocalData('friends'),
              _util.getLocalData('courses')),
          datumTokenizer: function(d) {
            return Bloodhound.tokenizers.whitespace(d.tokens.join(' '));
          },
          queryTokenizer: Bloodhound.tokenizers.whitespace
        });
        engine.initialize();
        setUpAutocomplete();
      };

      var setUpAutocomplete = function() {
        $('.search-bar').typeahead({
          hint: true,
          autoselect: true,
          highlight: true,
          minLength: 2,
          limit: 5
        },
        {
          name: 'friendsAndCourses',
          displayKey: itemName,
          source: engine.ttAdapter(),
          templates: {
            empty: _.template($('#empty-results-message-tpl').html()),
            suggestion: customSuggestionTemplate
          }
        })
        .on('typeahead:opened', onOpened)
        .on('typeahead:selected', onSelected);
      };

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
            initBloodhoundWithAutocomplete();
          }
        });
      } else {
        initBloodhoundWithAutocomplete();
      }
    }
  });

  return {
    SearchBarView: SearchBarView
  };
});
