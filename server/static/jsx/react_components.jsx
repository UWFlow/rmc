/** @jsx React.DOM */
define(['ext/react', 'util', 'moment'],
function(React, util, moment) {

  var CommentData = React.createClass({
    render: function() {
      var author;
      if (this.props.anon) {
        author = (
          <div>
          </div>
        );
      } else if (this.props.author.id) {
        author = (
          <span>
            <a href="/profile/{this.props.author.id.$oid">
              {this.props.author.name}
            </a>
            <span className="muted"> on </span>
          </span>
        );
      } else {
        var _user = require('user');
        var program = _user.getShortProgramName(
            this.props.author.program_name);
        author = (
          <span>
            <span className="muted">
              A {('aeiou'.indexOf(program[0].toLowerCase()) !== -1) ? 'n' : ''}
            </span>
            {program}
            <span className="muted"> student on </span>
          </span>
        );
      }
      var date = moment(this.props.date).format('MMM D, YYYY');
      return (
        <div>
          <small className="comment-date">
            {author}
            <span className="muted">
              {date}
            </span>
          </small>
        </div>
      );
    }
  });

  var Comment = React.createClass({
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
        <div className="row-fluid">
          <div className="span3 author">
            <img className="img-rounded" width="50" height="50"
                src={author_pic_url} className="author-pic" />
            <CommentData author={this.props.data.author} anon={anon}
                date={this.props.data.comment_date.$date}>
            </CommentData>
          </div>
          <div className="comment-text span9">
            {this.props.data.comment}
          </div>
        </div>
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

  var BinaryRating = React.createClass({
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
        <div className="row-fluid read-only">
          <span className="span5 choice-name">
            {_.str.capitalize(adjectiveMap[this.props.data.name]) + '?'}
          </span>
          <span className="span7 btn-group rating-choices">
            <button type="button" className={yes_btn_classes}>
              <i className="thumb-icon icon-thumbs-up"></i>
              Yes
            </button>
            <button type="button" className={no_btn_classes}>
              <i className="thumb-icon icon-thumbs-down"></i>
              No
            </button>
          </span>
        </div>
      );
    }
  });

  var RatingBox = React.createClass({
    render: function() {
      var ratings = this.props.data.map(function(rating) {
        return (
          <BinaryRating data={rating}></BinaryRating>
        );
      });
      return (
        <div>
          {ratings}
        </div>
      );
    }
  });

  var Review = React.createClass({
    render: function() {
      return (
        <div className="row-fluid">
          <div className="span8">
            <Comment data={this.props.data} />
          </div>
          <div className="span4">
            <RatingBox data={this.props.data.ratings} />
          </div>
        </div>
      )
    }
  });

  var ReviewList = React.createClass({
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
          <div className="review-post">
            <Review data={review}></Review>
          </div>
        );
      });
      return (
        <div>
          {reviewNodes}
        </div>
      );
    }
  });

  var ReviewBox = React.createClass({
    render: function() {
      return (
        <div>
          <h2 class="tip-title">Course Comments</h2>
          <ReviewList data={this.props.data}></ReviewList>
        </div>
      );
    }
  });

  var RatingRow = React.createClass({
    render: function() {
      if (this.props.data.name === 'overall') {
        return (<div></div>);
      }
      var barWidth = 42;
      var barStyle = {
        width: this.props.data.rating * 100 + "%"
      };
      return (
        <div className="row-fluid"
            title="People think this was helpful, maybe...">
          <div className="rating-name span2">
            {_.str.capitalize(adjectiveMap[this.props.data.name])}
          </div>
          <div className="rating-bar-span span6">
            <div className="shown-rating">
              <div className="rating-progress progress">
                <div className="rating-bar bar active positive bar-success"
                    style={barStyle}>
                </div>
              </div>
            </div>
          </div>
          <div className="span1 rating-num-span">
            {Math.round(this.props.data.rating * 100) + "%"}
          </div>
          <div className="shown-rating-num rating-count-span span3">
            <span className="muted"> {this.props.data.count} ratings</span>
          </div>
        </div>
      );
    }
  });

  var RatingsBox = React.createClass({
    render: function() {
      var ratingBars = this.props.data.map(function (ratingWithAttributes) {
        var rating = ratingWithAttributes;
        if (rating.attributes) {
          rating = rating.attributes;
        }

        return (
          <RatingRow data={rating} />
        );
      });

      return (
        <div className="ratings">
          {ratingBars}
        </div>
      );
    }
  });

  var MoreInfo = React.createClass({
    render: function() {
      return (
        <div className="row-fluid more-info">
          <div className="span12">
          </div>
        </div>
      );
    }
  });

  var CourseInnerView = React.createClass({
    render: function() {
      prereqs = (<div></div>);
      moreInfo = (<MoreInfo />);
      if (this.props.data.prereqs) {
        prereqs = (
          <p className="prereqs">
            <strong>Prereqs:</strong>
            {this.props.data.prereqs}
          </p>
        );
      }

      return (
        <div className="course-inner">
          <div className="row-fluid">
            <div className="span6 left-col">
              <p className="description">
               {this.props.data.description}
              </p>
              {prereqs}
            </div>
            <div className="span6 right-col">
              <RatingsBox data={this.props.data.ratings.models} />
            </div>
          </div>

          <MoreInfo />
        </div>
      );
    }
  });

  OverallRating = React.createClass({
    render: function() {
      var rating = this.props.data.rating;
      var count = this.props.data.count;
      if (this.props.data.count === 0) {
        rating = '--';
      } else {
        rating = (<span>{Math.round(rating * 100)}<sup className="percent">
                  %</sup></span>);
      }

      return (
        <div className="rating-box">
          <div className="rating">
            {rating}
          </div>
          <div className="num-ratings">
            {count} ratings
          </div>
        </div>
      );
    }
  });

  ProfCard = React.createClass({
    render: function() {
      var kittenNum = util.getKittenNumFromName(this.props.data.name);
      var pictureUrl = "/static/img/kittens/color/" + kittenNum + ".jpg";

      return (
        <div>
          <img width="150" height="150" className="prof-picture img-polaroid"
              src={pictureUrl} ></img>
          <div className="prof-info">
            <h3 className="prof-name">
              <a href="professor/{this.props.data.id}" className="prof-link">
                {this.props.data.name}
              </a>
            </h3>
            <dl className="dl-horizontal">
              <dt>Email</dt>
              <dd>Coming soon...</dd>
              <dt>Phone</dt>
              <dd>Coming soon...</dd>
              <dt>Office</dt>
              <dd>Coming soon...</dd>
            </dl>
          </div>
        </div>
      );
    }
  });

  ProfExpandableView = React.createClass({
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
      var expandLink = (<div></div>);
      if (this.getNumberHidden() > 0 || this.state.expanded) {
        var expandString;
        if (this.state.expanded) {
          expandString = "Hide " + (this.props.data.course_reviews.length -
              this.state.collapsedNum) + " reviews";
        } else {
          expandString = "Show " + this.getNumberHidden() + " reviews";
        }
        expandLink = (
          <a className="toggle-reviews"
              onClick={this.toggleExpanded}>{expandString}</a>);
      }

      return (
        <div className="well expandable-prof">
          <div className="row-fluid">
            <div className="span6">
              <ProfCard data={this.props.data}/>
            </div>
            <div className="span6">
              <div className="row-fluid">
                <div className="span12 prof-rating-container">
                  <OverallRating data={_.find(this.props.data.course_ratings,
                      function(rating) {
                        return rating.name === 'overall';
                      })} />
                </div>
              </div>
              <div className="row-fluid">
                <div className="span12">
                  <RatingsBox data={this.props.data.course_ratings} />
                </div>
              </div>
            </div>
          </div>
          <ReviewList data={this.props.data.course_reviews}
              numToHide={this.getNumberHidden()} />
          {expandLink}
        </div>
      );
    }
  });

  ProfCollection = React.createClass({
    render: function() {
      var profViews = this.props.data.map(function(profObj) {
        return (<ProfExpandableView data={profObj} />);
      });

      return (
        <div>
          {profViews}
        </div>
      );
    }
  });

  return {
    CourseInnerView: CourseInnerView,
    ReviewBox: ReviewBox,
    ProfCollection: ProfCollection
  };
});
