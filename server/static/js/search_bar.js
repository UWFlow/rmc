define(['ext/backbone', 'ext/jquery', 'ext/underscore', 'util'],
function(RmcBackbone, $, _, _util) {

  var duration = 400;
  var extraWidth;
  var baseWidth = 200;
  var moving = false;

  var programToString = function(program) {
    if (program) {
      return program;
    } else {
      return "";
    }
  };

  var formatCourseResult = function(course) {
    return '<a style="display:block;"><i class="icon-book search-icon"></i>'+
        '<b>'+course.label.toUpperCase()+'</b> &nbsp;&nbsp;&nbsp;&nbsp;'+
        course.name + '</a>';
  };

  var formatFriendResult = function(friend) {
    return '<a style="display:block;"><img src="'+friend.pic +
        '" width="20" height="20">'+'<b>'+friend.label+'</b> &nbsp;&nbsp;' +
        programToString(friend.program)+'</a>';
  };

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
      $(".search-div").animate({
        width: '+=' + extraWidth,
        duration: duration,
        queue: false
      },
      'easeOutCubic',
      function() {
        $(".search-div").width(extraWidth + baseWidth);
        moving = false;
      });
      $(".nav").hide({
        duration: duration,
        queue: false
      });
      $('search-bar').autocomplete("open");
    },
    onBlur: function(event){
      $('.search-div').css('opacity', 0.8);
      if (moving) {
        return;
      } else {
        moving = true;
      }
      $('.search-bar').attr('placeholder', 'Search courses/friends');
      $(".search-div").animate({
        width: '-=' + extraWidth,
        duration: duration,
        queue: false
      },
      'easeOutCubic',
      function() {
        $('search-div').width(baseWidth);
        moving = false;
      });
      $('.nav').show({
        duration: duration,
        queue: false
      });
      setTimeout(function() {
        $('search-bar').autocomplete('close');
      },0);
    },
    getData: function() {
      var toReturn;
      var result_types = [];
      if (!_util.getLocalData('courses')) {
        result_types.push('courses');
      }
      if (!_util.getLocalData('friends')) {
        result_types.push('friends');
      }
      result_types.join(',');
      var setUpAutocomplete = function() {
        $('.search-bar').autocomplete({
          source: $.merge($.merge([], _util.getLocalData('friends')),
              _util.getLocalData('courses')),
          minLength: 2,
          open: function() {
            $('.ui-menu').width(extraWidth +
                baseWidth);
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
                formatCourseResult(item));
          } else {
            toReturn = $('<li>').data('item.autocomplete', item).append(
                formatFriendResult(item));
          }
          toReturn.appendTo(ul);
        };
      };

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
            setUpAutocomplete();
          }
        });
      } else {
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
