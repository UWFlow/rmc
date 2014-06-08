define(['ext/backbone', 'ext/jquery', 'ext/underscore', 'util',
    'ext/typeahead'],
function(RmcBackbone, $, _, _util, _typeahead) {

  var duration = 400;
  var extraWidth;
  var baseWidth = 200;
  var moving = false;

  var substringMatcher = function(strs) {
    return function findMatches(q, cb) {
      var matches, substrRegex;

      // an array that will be populated with substring matches
      matches = [];

      // regex used to determine if a string contains the substring `q`
      substrRegex = new RegExp(q, 'i');

      // iterate through the pool of strings and for any string that
      // contains the substring `q`, add it to the `matches` array
      $.each(strs, function(i, str) {
        if (substrRegex.test(str)) {
          // the typeahead jQuery plugin expects suggestions to a
          // JavaScript object, refer to typeahead docs for more info
          matches.push({ value: str });
        }
      });

      cb(matches);
    };
  };

  var states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
    'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii',
    'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
    'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
    'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
    'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota',
    'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
    'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
    'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
  ];

  // var programToString = function(program) {
  //   if (program) {
  //     return program;
  //   } else {
  //     return "";
  //   }
  // };

  // var formatCourseResult = function(course) {
  //   return '<a style="display:block;"><i class="icon-book search-icon"></i>'+
  //       '<b>'+course.label.toUpperCase()+'</b> &nbsp;&nbsp;&nbsp;&nbsp;'+
  //       course.name + '</a>';
  // };

  // var formatFriendResult = function(friend) {
  //   return '<a style="display:block;"><img src="'+friend.pic +
  //       '" width="20" height="20">'+'<b>'+friend.label+'</b> &nbsp;&nbsp;' +
  //       programToString(friend.program)+'</a>';
  // };

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
    },
    getData: function() {
      //var toReturn;
      var result_types = [];
      if (!_util.getLocalData('courses')) {
        result_types.push('courses');
      }
      if (!_util.getLocalData('friends')) {
        result_types.push('friends');
      }
      result_types.join(',');
      var setUpAutocomplete = function() {
        $('.search-bar').typeahead({
          hint: true,
          highlight: true,
          minLength: 1,
          template: '<li > <a style="display:block;"><i class="icon-book' +
          'search-icon"></i><b>{{value}}</b>&nbsp;&nbsp;&nbsp;&nbsp;</a></li>'
        },
        {
          name: 'states',
          displayKey: 'value',
          source: substringMatcher(states)
        });
      };
      setUpAutocomplete();
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
