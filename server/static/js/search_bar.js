/*global Bloodhound, Handlebars */

define(['ext/backbone', 'ext/jquery', 'ext/underscore', 'util',
    'ext/typeahead', 'ext/handlebars'],
function(RmcBackbone, $, _, _util, _typeahead) {

  var duration = 400;
  var extraWidth;
  var baseWidth = 200;
  var moving = false;

  var SearchBarView = RmcBackbone.View.extend({
    initialize: function() {
      extraWidth = $('ul.pull-right').width();
    },
    render: function() {
      var template = _.template($('#search-bar-tpl').html());
      this.$el.html(template);
    },
    events: {
      'focus input[type=text]': 'onFocus',
      'blur input[type=text]': 'onBlur',
      'keydown .search-bar': 'onSearchBoxKeyDown'
    },
    onFocus: function(event){
      $('.search-div').css('opacity', 1.0);
      if (moving) {
        return;
      } else {
        moving = true;
      }
      $('.search-bar').attr('placeholder', '');
      if ($('.twitter-typeahead').width() !== (extraWidth+baseWidth)) {
        $('.twitter-typeahead').animate({
          width: '+=' + extraWidth,
          duration: duration,
          queue: false
        },
        'easeOutCubic',
        function() {
          $(".twitter-typeahead").width(extraWidth + baseWidth);
          moving = false;
        });
        $(".nav.pull-right").hide({
          duration: duration,
          queue: false
        });
        $('.search-div').animate({
          width: '+=' + extraWidth,
          duration: duration,
          queue: false
        },
        'easeOutCubic',
        function() {
          $('.search-div').width(extraWidth + baseWidth);
          moving = false;
          $('.twitter-typeahead').typeahead('open');
        });
      }
    },
    onBlur: function(event){
      $('.search-div').css('opacity', 0.8);
      if (moving) {
        return;
      } else {
        moving = true;
      }
      if ($('.twitter-typeahead').width() !== baseWidth) {
        $('.twitter-typeahead').animate({
          width: '-=' + extraWidth,
          duration: duration,
          queue: false
        },
        'easeOutCubic',
        function() {
          $('.twitter-typeahead').width(baseWidth);
          moving = false;
        });
        $('.nav.pull-right').show({
          duration: duration,
          queue: false
        });
        $('.search-div').animate({
          width: '-=' + extraWidth,
          duration: duration,
          queue: false
        },
        'easeOutCubic',
        function() {
          $('.search-div').width(baseWidth);
          moving = false;
        });
      }
    },
    getData: function() {
      var result_types = [];
      if (!_util.getLocalData('courses')) {
        result_types.push('courses');
      }
      if (!_util.getLocalData('friends')) {
        result_types.push('friends');
      }
      result_types.join(',');

      var onOpened = function($e) {
        $('.tt-dropdown-menu').css('width', baseWidth+extraWidth);
      };

      var onselected = function(event, datum, name) {
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
          formatter = Handlebars.compile('<div><p class="image-paragraph">' +
              '<img src="/static/img/book_image.png" class="' +
              'search-icon"></p><span class="primary-title">' +
              '<p> {{department_id}} {{number}} </p>' + '</span>' +
              '<span class="secondary-title"><p>{{name}}</p></span></div>');
          item.department_id = item.department_id.toUpperCase();
        } else if (item.type === 'friend') {
          console.log(item.program);
          if (item.program == null) {
            formatter = Handlebars.compile('<div><p class=' +
                '"image-paragraph-profile"><img src={{pic}} class="' +
                'profile-pic"></p><span class="primary-title"> <p> {{label}}' +
                '</p> </span><span class="secondary-title"><p> &nbsp; </p>' +
                '</span></div>');
          } else {
            formatter = Handlebars.compile('<div><p class=' +
                '"image-paragraph-profile"><img src={{pic}} class="' +
                'profile-pic"></p><span class="primary-title"> <p> {{label}}' +
                '</p></span><span class="secondary-title"><p>{{program}}</p>' +
                '</span></div>');
          }
        }
        return formatter(item);
      };

      var setUpAutocomplete = function() {
        $('.search-bar').typeahead({
          hint: true,
          autoselect: true,
          highlight: true,
          minLength: 2,
          limit: 5,
        },
        {
          name: 'friendsAndCourses',
          displayKey: itemName,
          source: engine.ttAdapter(),
          templates: {
            empty: '<div class="empty-message"><span style="display:block;">'+
            '<p> No results found </p></span></div>',
            suggestion: customSuggestionTemplate
          }
        })
        .on('typeahead:opened', onOpened)
        .on('typeahead:selected', onselected);
        $('.icon-search').zIndex(1);
      };
      var engine;
      if (result_types.length > 0) {
        $.ajax({
          dataType: 'json',
          url: '/api/v1/search/bar?result_types=' + result_types,
          success: function(data) {
            if (result_types.indexOf('courses') >= 0) {
               // 12096e5 = 2 weeks in milliseconds
              _util.storeLocalData('courses', data.courses,
                  +(new Date()) + 12096e5);
            }
            if (result_types.indexOf('friends') >= 0) {
               // 86400000 is 1 day in milliseconds
              _util.storeLocalData('friends', data.friends,
                  +(new Date()) + 86400000);
            }
            engine = new Bloodhound({
              name: 'friendsAndCourses',
              local: $.merge($.merge([], _util.getLocalData('friends')),
                  _util.getLocalData('courses')),
              datumTokenizer: function(d) {
                return Bloodhound.tokenizers.whitespace(d.tokens.join(' '));
              },
              queryTokenizer: Bloodhound.tokenizers.whitespace
            });
            engine.initialize();
            setUpAutocomplete();
          }
        });
      } else {
        engine = new Bloodhound({
          name: 'friendsAndCourses',
          local: $.merge($.merge([], _util.getLocalData('friends')),
              _util.getLocalData('courses')),
          datumTokenizer: function(d) {
            return Bloodhound.tokenizers.whitespace(d.tokens.join(' '));
          },
          queryTokenizer: Bloodhound.tokenizers.whitespace
        });
        engine.initialize();
        setUpAutocomplete();
      }
    },
    onSearchBoxKeyDown: function(e) {
      if (e.keyCode === 9) {  //tab pressed
        e.preventDefault(); // stops its action
      }
    }
  });

  return {
    SearchBarView: SearchBarView
  };
});
