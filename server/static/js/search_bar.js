define(['ext/backbone', 'ext/jquery', 'ext/underscore',
    'ext/jqueryautocomplete'],
function(RmcBackbone, $, _) {
  var SearchBar = RmcBackbone.View.extend({
    initialize: function() {
      SearchBar.duration = 300;
      SearchBar.extraWidth = $('.nav').width();
      SearchBar.baseWidth = 75;
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
      var availableTags = [
        "ActionScript",
        "AppleScript",
        "Asp",
        "BASIC",
        "C",
        "C++",
        "Clojure",
        "COBOL",
        "ColdFusion",
        "Erlang",
        "Fortran",
        "Groovy",
        "Haskell",
        "Java",
        "JavaScript",
        "Lisp",
        "Perl",
        "PHP",
        "Python",
        "Ruby",
        "Scala",
        "Scheme"
      ];
      $( ".search-bar" ).autocomplete({
        source: availableTags,
        open: function() {
          $('.ui-menu').width(SearchBar.extraWidth+SearchBar.baseWidth);
          $('ul.ui-autocomplete').css({'list-style': 'none'});
        }
      });
    },
    onBlur: function( event ){
      console.log("Blurred!");
      if (SearchBar.moving) {
        return;
      } else {
        SearchBar.moving = true;
      }
      $('.search-bar').attr('placeholder', 'Search');
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
    setAutocomplete: function() {
      var availableTags = [
        "ActionScript",
        "AppleScript",
        "Asp",
        "BASIC",
        "C",
        "C++",
        "Clojure",
        "COBOL",
        "ColdFusion",
        "Erlang",
        "Fortran",
        "Groovy",
        "Haskell",
        "Java",
        "JavaScript",
        "Lisp",
        "Perl",
        "PHP",
        "Python",
        "Ruby",
        "Scala",
        "Scheme"
      ];
      $( ".search-bar" ).autocomplete({
        source: availableTags,
        open: function() {
          // After menu has been opened, set width to 100px
          $('.ui-menu')
              .width(100);
        },
        delay: 0,
        autoFocus: true
      });
      $('.ui-autocomplete').css({'background-color': '#ffffff',
          _width: '100px'});
    },
    onSearchBoxKeyDown: function(e) {
      console.log(e);
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
