define(function(require) {
  var RmcBackbone = require('rmc_backbone');
  var $ = require('ext/jquery');
  var _ = require('ext/underscore');

  var SearchBar = RmcBackbone.View.extend({
    initialize: function() {
      this.duration = 300;
      this.extraWidth = $('.nav').width();
      this.baseWidth = 75;
    },
    render: function() {
      var template = _.template($('#search-bar-tpl').html());
      this.$el.html(template);
    },
    events: {
      "focus input[type=text]": "onFocus",
      "blur input[type=text]": "onBlur"
    },
    onFocus: function( event ){
      console.log("Focused!");
      $('.search-bar').attr('placeholder', '');
      $(".search-div").animate({
        width: '+='+this.extraWidth.toString()
      },
      { duration: this.duration , queue: false },
      'easeOutCubic',
      function() {
        $(".search-div").width(this.extraWidth+this.baseWidth);
      });
      $(".nav").hide({duration: this.duration , queue: false});
    },
    onBlur: function( event ){
      console.log("Blurred!");
      $('.search-bar').attr('placeholder', 'Search');
      $(".search-div").animate({
        width: '-='+this.extraWidth.toString()
      },
      { duration: this.duration , queue: false },
      'easeOutCubic',
      function() {
        $(".search-div").width(this.baseWidth);
      });
      $(".nav").show({duration: this.duration , queue: false});
    }
  });

  return {
    SearchBar: SearchBar
  };
});
