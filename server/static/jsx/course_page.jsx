/** @jsx React.DOM */
require(
['ext/jquery','course', 'took_this', 'user', 'tips', 'prof', 'exam', 'ratings',
  'user_course', 'review', 'sign_in', 'ext/react', 'util', 'moment'],
function($, course, tookThis, user, tips, prof, _exam, ratings, user_course,
    _review, _sign_in, React, util, moment) {

  course.CourseCollection.addToCache(pageData.courseObj);
  user_course.UserCourses.addToCache(pageData.userCourseObjs);
  prof.ProfCollection.addToCache(pageData.professorObjs);

  var courseObj = pageData.courseObj;
  var courseModel = course.CourseCollection.getFromCache(courseObj.id);
  var userCourse = courseModel.get('user_course');

  var overallRating = courseModel.getOverallRating();
  var ratingBoxView = new ratings.RatingBoxView({ model: overallRating });
  $('#rating-box-container').html(ratingBoxView.render().el);

  var courseInnerView = new course.CourseInnerView({
    courseModel: courseModel,
    userCourse: userCourse,
    shouldLinkifySectionProfs: true
  });
  $('#course-inner-container').html(courseInnerView.render().el);
  courseInnerView.animateBars();

  if (window.pageData.examObjs.length) {
    var examCollection = new _exam.ExamCollection(window.pageData.examObjs);

    // Only show this "final exams" section if there are actually exams taking
    // place in the future
    if (examCollection.latestExam().get('end_date') >= new Date()) {
      var examSchedule = new _exam.ExamSchedule({
        exams: examCollection,
        last_updated_date: window.pageData.examUpdatedDate
      });
      var courseExamScheduleView = new _exam.CourseExamScheduleView({
        examSchedule: examSchedule
      });

      $('#exam-info-container')
        .html(courseExamScheduleView.render().el)
        .show();
    }
  }

  var tookThisSidebarView = new tookThis.TookThisSidebarView({
    userCourses: courseModel.get('friend_user_courses'),
    courseCode: courseModel.get('code'),
    currentTermId: window.pageData.currentTermId
  });
  $('#took-this-sidebar-container').html(tookThisSidebarView.render().el);

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
          <div>
            <a href="/profile/{this.props.author.id.$oid">
              {this.props.author.name}
            </a>
            <span className="muted"> on </span>
          </div>
        );
      } else {
        var _user = require('user');
        var program = _user.getShortProgramName(
            this.props.author.program_name);
        author = (
          <div>
          <span className="muted">
            A {('aeiou'.indexOf(program[0].toLowerCase()) !== -1) ? 'n' : ''}
          </span>
          {program}
          <span className="muted"> student on</span>
          </div>
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
            <img class="img-rounded" width="50" height="50"
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
    render: function() {
      var sortedReviews =  _.sortBy(this.props.data,
          function(r) {
            return -r.comment_date.$date;
          }
      );

      var reviewNodes = sortedReviews.map(function (review) {
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

  React.renderComponent(
    <ReviewBox data={window.pageData.tipObjs} />,
    document.getElementById('tips-collection-container')
  );

  // TODO(david): Handle no professors for course
  var profsCollection = courseModel.get('professors');
  var profsView = new prof.ProfCollectionView({ collection: profsCollection });
  $('#professor-review-container').html(profsView.render().el);

  if (!window.pageData.currentUserId) {
    _sign_in.renderBanner({
      source: 'BANNER_COURSE_PAGE',
      nextUrl: window.location.href
    });
  }

  mixpanel.track('Impression: Single course page');

  $(document.body).trigger('pageScriptComplete');
});
