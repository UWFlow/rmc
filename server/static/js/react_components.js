/** @jsx React.DOM */
define(['ext/react', 'util', 'moment'],
function(React, util, moment) {

  var CommentData = React.createClass({displayName: 'CommentData',
    render: function() {
      var author;
      if (this.props.anon) {
        author = (
          React.DOM.div(null
          )
        );
      } else if (this.props.author.id) {
        author = (
          React.DOM.div(null, 
            React.DOM.a({href: "/profile/{this.props.author.id.$oid"}, 
              this.props.author.name
            ), 
            React.DOM.span({className: "muted"}, " on ")
          )
        );
      } else {
        var _user = require('user');
        var program = _user.getShortProgramName(
            this.props.author.program_name);
        author = (
          React.DOM.div(null, 
          React.DOM.span({className: "muted"}, 
            "A ", ('aeiou'.indexOf(program[0].toLowerCase()) !== -1) ? 'n' : ''
          ), 
          program, 
          React.DOM.span({className: "muted"}, " student on")
          )
        );
      }
      var date = moment(this.props.date).format('MMM D, YYYY');
      return (
        React.DOM.div(null, 
          React.DOM.small({className: "comment-date"}, 
            author, 
            React.DOM.span({className: "muted"}, 
              date
            )
          )
        )
      );
    }
  });

  var Comment = React.createClass({displayName: 'Comment',
    getAnonAvatar: function() {
      var kittenNum = util.getHashCode(this.props.data.comment) %
          pageData.NUM_KITTENS;
      return '/static/img/kittens/grey/' + kittenNum + '.jpg';
    },

    getProgramAvatar: function() {
      var programName = (this.props.data.author || {}).program_name;
      var kittenNum = util.getHashCode('' + programName) %
                pageData.NUM_KITTENS;
      return '/static/img/kittens/grey/' + kittenNum + '.jpg';
    },

    render: function() {
      var author_pic_url;
      var anon = false;
      if (this.props.data.author) {
        if (this.props.data.author.profile_pic_url) {
          author_pic_url = this.props.data.author.profile_pic_url;
        } else if (this.props.data.author.program_name) {
          author_pic_url = this.getProgramAvatar();
        } else {
          author_pic_url = this.getAnonAvatar()
          anon = true;
        }
      } else {
        author_pic_url = this.getAnonAvatar();
        anon = true;
      }

      return (
        React.DOM.div({className: "row-fluid"}, 
          React.DOM.div({className: "span3 author"}, 
            React.DOM.img({className: "img-rounded", width: "50", height: "50", 
                src: author_pic_url, className: "author-pic"}), 
            CommentData({author: this.props.data.author, anon: anon, 
                date: this.props.data.comment_date.$date}
            )
          ), 
          React.DOM.div({className: "comment-text span9"}, 
            this.props.data.comment
          )
        )
      );
    }
  });

  var adjectiveMap = {
    'interest': 'Liked it',
    'easiness': 'easy',
    'usefulness': 'useful',
    'clarity': 'clear',
    'passion': 'engaging',
    '': ''
  };

  var BinaryRating = React.createClass({displayName: 'BinaryRating',
    render: function() {
      var cx = React.addons.classSet;
      var yes_btn_classes = cx({
        'btn yes-btn disabled': true,
        'active btn-success': this.props.data.rating === 1
      });
      var no_btn_classes = cx({
        'btn no-btn disabled': true,
        'active btn-danger': this.props.data.rating === 0
      });
      return (
        React.DOM.div({className: "row-fluid read-only"}, 
          React.DOM.span({className: "span5 choice-name"}, 
            _.str.capitalize(adjectiveMap[this.props.data.name]) + '?'
          ), 
          React.DOM.span({className: "span7 btn-group rating-choices"}, 
            React.DOM.button({type: "button", className: yes_btn_classes}, 
              React.DOM.i({className: "thumb-icon icon-thumbs-up"}), 
              "Yes"
            ), 
            React.DOM.button({type: "button", className: no_btn_classes}, 
              React.DOM.i({className: "thumb-icon icon-thumbs-down"}), 
              "No"
            )
          )
        )
      );
    }
  });

  var RatingBox = React.createClass({displayName: 'RatingBox',
    render: function() {
      var ratings = this.props.data.map(function(rating) {
        return (
          BinaryRating({data: rating})
        );
      });
      return (
        React.DOM.div(null, 
          ratings
        )
      );
    }
  });

  var Review = React.createClass({displayName: 'Review',
    render: function() {
      return (
        React.DOM.div({className: "row-fluid"}, 
          React.DOM.div({className: "span8"}, 
            Comment({data: this.props.data})
          ), 
          React.DOM.div({className: "span4"}, 
            RatingBox({data: this.props.data.ratings})
          )
        )
      )
    }
  });

  var ReviewList = React.createClass({displayName: 'ReviewList',
    render: function() {
      var sortedReviews =  _.sortBy(this.props.data,
          function(r) {
            return -r.comment_date.$date;
          }
      );

      var reviewNodes = sortedReviews.map(function (review) {
        return (
          React.DOM.div({className: "review-post"}, 
            Review({data: review})
          )
        );
      });
      return (
        React.DOM.div(null, 
          reviewNodes
        )
      );
    }
  });

  var ReviewBox = React.createClass({displayName: 'ReviewBox',
    render: function() {
      return (
        React.DOM.div(null, 
          React.DOM.h2({class: "tip-title"}, "Course Comments"), 
          ReviewList({data: this.props.data})
        )
      );
    }
  });

  var RatingRow = React.createClass({displayName: 'RatingRow',
    render: function() {
      var barWidth = 42;
      var barStyle = {
        width: this.props.data.rating * 100 + "%"
      };
      console.log(this.props.data);
      return (
        React.DOM.div({className: "row-fluid", 
            title: "People think this was helpful, maybe..."}, 
          React.DOM.div({className: "rating-name span2"}, 
            _.str.capitalize(adjectiveMap[this.props.data.name])
          ), 
          React.DOM.div({className: "rating-bar-span span6"}, 
            React.DOM.div({className: "shown-rating"}, 
              React.DOM.div({className: "rating-progress progress"}, 
                React.DOM.div({className: "rating-bar bar active positive bar-success", 
                    style: barStyle}
                )
              )
            )
          ), 
          React.DOM.div({className: "span1 rating-num-span"}, 
            Math.round(this.props.data.rating * 100) + "%"
          ), 
          React.DOM.div({className: "shown-rating-num rating-count-span span3"}, 
            React.DOM.span({className: "muted"}, " ", this.props.data.count, " ratings")
          )
        )
      );
    }
  });

  var RatingsBox = React.createClass({displayName: 'RatingsBox',
    render: function() {
      var ratingBars = this.props.data.map(function (ratingWithAttributes) {
        var rating = ratingWithAttributes.attributes;
        return (
          RatingRow({data: rating})
        );
      });

      return (
        React.DOM.div({className: "ratings"}, 
          ratingBars
        )
      );
    }
  });

  var MoreInfo = React.createClass({displayName: 'MoreInfo',
    render: function() {
      return (
        React.DOM.div({className: "row-fluid more-info"}, 
          React.DOM.div({className: "span12"}
          )
        )
      );
    }
  });

  var CourseInnerView = React.createClass({displayName: 'CourseInnerView',
    render: function() {
      prereqs = (React.DOM.div(null));
      moreInfo = (MoreInfo(null));
      if (this.props.data.prereqs) {
        prereqs = (
          React.DOM.p({className: "prereqs"}, 
            React.DOM.strong(null, "Prereqs:"), 
            this.props.data.prereqs
          )
        );
      }

      return (
        React.DOM.div({className: "course-inner"}, 
          React.DOM.div({className: "row-fluid"}, 
            React.DOM.div({className: "span6 left-col"}, 
              React.DOM.p({className: "description"}, 
               this.props.data.description
              ), 
              prereqs
            ), 
            React.DOM.div({className: "span6 right-col"}, 
              RatingsBox({data: this.props.data.ratings.models})
            )
          ), 

          MoreInfo(null)
        )
      );
    }
  });



  return {
    CourseInnerView: CourseInnerView,
    ReviewBox: ReviewBox
  };
});
