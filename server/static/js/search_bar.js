define(['ext/backbone', 'ext/jquery', 'ext/underscore', 'util',
    'search_bar_util'],
function(RmcBackbone, $, _, _util, _search_util) {
  var SearchBar = RmcBackbone.View.extend({
    initialize: function() {
      SearchBar.duration = 300;
      SearchBar.extraWidth = $('.nav').width();
      SearchBar.baseWidth = 200;
      SearchBar.moving = false;
    },
    render: function() {
      var template = _.template($('#search-bar-tpl').html());
      this.$el.html(template);
    },
    events: {
      "focus input[type=text]": "onFocus",
      "blur input[type=text]": "onBlur",
      'keydown .search-bar': 'onSearchBoxKeyDown'
    },
    onFocus: function( event ){
      console.log("Focused!");
      $('.search-div').css('opacity','1.0');
      if (SearchBar.moving) {
        return;
      } else {
        SearchBar.moving = true;
      }
      $('.search-bar').attr('placeholder', '');
      $(".search-div").animate({
        width: '+='+SearchBar.extraWidth.toString(),
        duration: SearchBar.duration,
        queue: false
      },
      'easeOutCubic',
      function() {
        $(".search-div").width(SearchBar.extraWidth+SearchBar.baseWidth);
        SearchBar.moving = false;
      });
      $(".nav").hide({duration: this.duration , queue: false});
      $('search-bar').autocomplete("open");
    },
    onBlur: function( event ){
      console.log("Blurred!");
      $('.search-div').css('opacity','0.8');
      if (SearchBar.moving) {
        return;
      } else {
        SearchBar.moving = true;
      }
      $('.search-bar').attr('placeholder', 'Search courses/friends');
      $(".search-div").animate({
        width: '-='+SearchBar.extraWidth.toString(),
        duration: SearchBar.duration,
        queue: false
      },
      'easeOutCubic',
      function() {
        $(".search-div").width(SearchBar.baseWidth);
        SearchBar.moving = false;
      });
      $(".nav").show({duration: this.duration , queue: false});
      setTimeout(function() {
        $('search-bar').autocomplete("close");
      },0);
    },
    getData: function() {
      var dataNeeded = '';
      var toReturn;
      if (!_util.getLocalData('courses')) {
        dataNeeded += 'c';
      }
      if (!_util.getLocalData('friends')) {
        dataNeeded += 'f';
      }
      $.ajax({
        dataType: "json",
        url: 'http://localhost:5000/api/v1/search/bar?dataNeeded='+dataNeeded,
        success: function(data) {
          if (dataNeeded === 'c' || dataNeeded === 'cf') {
            _util.storeLocalData('courses', data.courses, +Date()+12096e5);
          }
          if (dataNeeded === 'f' || dataNeeded === 'f') {
            _util.storeLocalData('friends', data.friends, +Date()+86400000);
          }
          $( ".search-bar" ).autocomplete({
            source: $.merge($.merge([], _util.getLocalData('friends')),
                _util.getLocalData('courses')),
            minLength: 2,
            open: function() {
              $('.ui-menu').width(SearchBar.extraWidth+SearchBar.baseWidth);
              $('ul.ui-autocomplete').css({'list-style': 'none'});
            },
            delay: 0,
            autoFocus: true,
            select: function( event, ui ) {
              if (ui.item.type ==='course') {
                window.location.href="/courses/"+ui.item.label;
              } else {
                window.location.href="/profile/"+ui.item.id;
              }
            }
          })
          .data('autocomplete')._renderItem = function(ul, item) {
            if (item.type === 'course') {
              toReturn =$('<li>').data('item.autocomplete', item).append(
                  _search_util.formatCourseResult(item));
            } else {
              toReturn =$('<li>').data('item.autocomplete', item).append(
                  _search_util.formatFriendResult(item));
            }
            toReturn.appendTo(ul);
          };
        }
      });
    },
    onSearchBoxKeyDown: function(e) {
      if (e.keyCode === 9) {  //tab pressed
        console.log("TAB pressed");
        e.preventDefault(); // stops its action
      }
    }
  });

  return {
    SearchBar: SearchBar
  };
});
