define(['ext/backbone', 'ext/jquery', 'ext/underscore', 'util',
    'search_bar_util'],
function(RmcBackbone, $, _, _util, _search_util) {
  var SearchBarView = RmcBackbone.View.extend({
    initialize: function() {
      SearchBarView.duration = 400;
      SearchBarView.extraWidth = $('.nav').width();
      SearchBarView.baseWidth = 200;
      SearchBarView.moving = false;
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
      if (SearchBarView.moving) {
        return;
      } else {
        SearchBarView.moving = true;
      }
      $('.search-bar').attr('placeholder', '');
      $(".search-div").animate({
        width: '+=' + SearchBarView.extraWidth,
        duration: SearchBarView.duration,
        queue: false
      },
      'easeOutCubic',
      function() {
        $(".search-div").width(SearchBarView.extraWidth +
            SearchBarView.baseWidth);
        SearchBarView.moving = false;
      });
      $(".nav").hide({
        duration: SearchBarView.duration,
        queue: false
      });
      $('search-bar').autocomplete("open");
    },
    onBlur: function(event){
      $('.search-div').css('opacity', 0.8);
      if (SearchBarView.moving) {
        return;
      } else {
        SearchBarView.moving = true;
      }
      $('.search-bar').attr('placeholder', 'Search courses/friends');
      $(".search-div").animate({
        width: '-=' + SearchBarView.extraWidth,
        duration: SearchBarView.duration,
        queue: false
      },
      'easeOutCubic',
      function() {
        $('search-div').width(SearchBarView.baseWidth);
        SearchBarView.moving = false;
      });
      $('.nav').show({
        duration: SearchBarView.duration,
        queue: false
      });
      setTimeout(function() {
        $('search-bar').autocomplete('close');
      },0);
    },
    getData: function() {
      var result_types = '';
      var toReturn;
      if (!_util.getLocalData('courses')) {
        result_types += 'courses,';
      }
      if (!_util.getLocalData('friends')) {
        result_types += 'friends,';
      }
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
          $('.search-bar').autocomplete({
            source: $.merge($.merge([], _util.getLocalData('friends')),
                _util.getLocalData('courses')),
            minLength: 2,
            open: function() {
              $('.ui-menu').width(SearchBarView.extraWidth +
                  SearchBarView.baseWidth);
              $('ul.ui-autocomplete').css({'list-style': 'none'});
            },
            delay: 0,
            autoFocus: true,
            select: function( event, ui ) {
              if (ui.item.type === 'course') {
                window.location.href = '/courses/' + ui.item.label;
              } else {
                window.location.href = '/profile/' + ui.item.id;
              }
            }
          })
          .data('autocomplete')._renderItem = function(ul, item) {
            if (item.type === 'course') {
              toReturn = $('<li>').data('item.autocomplete', item).append(
                  _search_util.formatCourseResult(item));
            } else {
              toReturn = $('<li>').data('item.autocomplete', item).append(
                  _search_util.formatFriendResult(item));
            }
            toReturn.appendTo(ul);
          };
        }
      });
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
