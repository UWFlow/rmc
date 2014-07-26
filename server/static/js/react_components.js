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
          React.DOM.span(null, 
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
          React.DOM.span(null, 
            React.DOM.span({className: "muted"}, 
              "A ", ('aeiou'.indexOf(program[0].toLowerCase()) !== -1) ? 'n' : ''
            ), 
            program, 
            React.DOM.span({className: "muted"}, " student on ")
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
    getDefaultProps: function() {
      return {
        numToHide: 0
      };
    },

    render: function() {
      var sortedReviews =  _.sortBy(this.props.data,
          function(r) {
            return -r.comment_date.$date;
          }
      );

      var reviewNodes = _.initial(sortedReviews, this.props.numToHide).map(
          function (review) {
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
      if (this.props.data.name === 'overall') {
        return (React.DOM.div(null));
      }
      var barWidth = 42;
      var barStyle = {
        width: this.props.data.rating * 100 + "%"
      };
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
        var rating = ratingWithAttributes;
        if (rating.attributes) {
          rating = rating.attributes;
        }

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

  OverallRating = React.createClass({displayName: 'OverallRating',
    render: function() {
      var rating = this.props.data.rating;
      var count = this.props.data.count;
      if (this.props.data.count === 0) {
        rating = '--';
      } else {
        rating = (React.DOM.span(null, Math.round(rating * 100), React.DOM.sup({className: "percent"}, 
                  "%")));
      }

      return (
        React.DOM.div({className: "rating-box"}, 
          React.DOM.div({className: "rating"}, 
            rating
          ), 
          React.DOM.div({className: "num-ratings"}, 
            count, " ratings"
          )
        )
      );
    }
  });

  ProfCard = React.createClass({displayName: 'ProfCard',
    render: function() {
      var kittenNum = util.getKittenNumFromName(this.props.data.name);
      var pictureUrl = "/static/img/kittens/color/" + kittenNum + ".jpg";

      return (
        React.DOM.div(null, 
          React.DOM.img({width: "150", height: "150", className: "prof-picture img-polaroid", 
              src: pictureUrl}), 
          React.DOM.div({className: "prof-info"}, 
            React.DOM.h3({className: "prof-name"}, 
              React.DOM.a({href: "professor/{this.props.data.id}", className: "prof-link"}, 
                this.props.data.name
              )
            ), 
            React.DOM.dl({className: "dl-horizontal"}, 
              React.DOM.dt(null, "Email"), 
              React.DOM.dd(null, "Coming soon..."), 
              React.DOM.dt(null, "Phone"), 
              React.DOM.dd(null, "Coming soon..."), 
              React.DOM.dt(null, "Office"), 
              React.DOM.dd(null, "Coming soon...")
            )
          )
        )
      );
    }
  });

  ProfExpandableView = React.createClass({displayName: 'ProfExpandableView',
    getInitialState: function() {
      return {
        expanded: false,
        collapsedNum: 3
      };
    },

    getNumberHidden: function() {
      if (this.state.expanded) {
        return 0;
      } else {
        return this.props.data.course_reviews.length - this.state.collapsedNum;
      }
    },

    toggleExpanded: function() {
      this.setState({expanded: !this.state.expanded});
    },

    render: function() {
      var expandLink = (React.DOM.div(null));
      if (this.getNumberHidden() > 0 || this.state.expanded) {
        var expandString;
        if (this.state.expanded) {
          expandString = "Hide " + (this.props.data.course_reviews.length -
              this.state.collapsedNum) + " reviews";
        } else {
          expandString = "Show " + this.getNumberHidden() + " reviews";
        }
        expandLink = (
          React.DOM.a({className: "toggle-reviews", 
              onClick: this.toggleExpanded}, expandString));
      }

      return (
        React.DOM.div({className: "well expandable-prof"}, 
          React.DOM.div({className: "row-fluid"}, 
            React.DOM.div({className: "span6"}, 
              ProfCard({data: this.props.data})
            ), 
            React.DOM.div({className: "span6"}, 
              React.DOM.div({className: "row-fluid"}, 
                React.DOM.div({className: "span12 prof-rating-container"}, 
                  OverallRating({data: _.find(this.props.data.course_ratings,
                      function(rating) {
                        return rating.name === 'overall';
                      })})
                )
              ), 
              React.DOM.div({className: "row-fluid"}, 
                React.DOM.div({className: "span12"}, 
                  RatingsBox({data: this.props.data.course_ratings})
                )
              )
            )
          ), 
          ReviewList({data: this.props.data.course_reviews, 
              numToHide: this.getNumberHidden()}), 
          expandLink
        )
      );
    }
  });

  ProfCollection = React.createClass({displayName: 'ProfCollection',
    render: function() {
      var profViews = this.props.data.map(function(profObj) {
        return (ProfExpandableView({data: profObj}));
      });

      return (
        React.DOM.div(null, 
          profViews
        )
      );
    }
  });

  return {
    CourseInnerView: CourseInnerView,
    ReviewBox: ReviewBox,
    ProfCollection: ProfCollection
  };
});
