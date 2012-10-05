require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'course', 'ext/bootstrap', 'rmc_backbone', 'user', 'user_course', 'course', 'prof'],
function($, _, _s, course, __, RmcBackbone, user, _user_course, _course, _prof) {

  var FETCH_DELAY_MS = 300;

  var CourseSearchView = RmcBackbone.View.extend({
    className: 'course-search',
    timer: undefined,
    keywords: undefined,
    sortMode: undefined,
    direction: undefined,
    count: 10,
    offset: 0,
    courses: undefined,
    hasMore: true,

    initialize: function(options) {
      this.sortMode = window.pageData.sortModes[0];
      this.setDirection(this.sortMode.direction);
      this.courses = new _course.CourseCollection();
      $(window).scroll(_.bind(this.scrollWindow, this));
    },

    scrollWindow: function(evt) {
      var loaderOffset = this.$('.loader-bottom').offset().top;
      var $window = $(window);
      var bottomOffset = $window.scrollTop() + $window.height();
      if (bottomOffset > loaderOffset) {
        this.updateCourses();
      }
    },

    render: function() {
      var sortModes = window.pageData.sortModes;
      this.$el.html(_.template($('#search-form-tpl').html(), {
        sortModes: sortModes,
        selectedSortMode: this.sortMode,
        selectedDirection: this.direction
      }));

      $('.dropdown-toggle').dropdown();
      var courseCollectionView = new _course.CourseCollectionView({
        courses: this.courses
      });
      this.$('.course-collection-placeholder').replaceWith(
          courseCollectionView.render().$el);
      this.updateCourses();

      window.setTimeout(_.bind(function() {
        // TODO(mack): investgate why this has to be done in window.setTimeout
        this.$('.keywords').focus();
      }, this), 0);

      return this;
    },

    events: {
      'click .sort-mode-dropdown .dropdown-menu li': 'changeSortMode',
      'click .order-dropdown .dropdown-menu li': 'changeDirection',
      'input .keywords': 'changeKeywords',
      'paste .keywords': 'changeKeywords'
    },

    changeSortMode: function(evt) {
      var $target = $(evt.currentTarget);
      this.$('.selected-sort-mode').text($target.text());
      var sortValue = $target.attr('data-value');
      this.sortMode = _.find(window.pageData.sortModes, function(sortMode) {
        return sortValue === sortMode.value;
      }, this);
      this.setDirection(this.sortMode.direction);
      this.$('.selected-direction').text(this.direction.name);

      this.resetAndUpdate();
    },

    changeDirection: function(evt) {
      var $target = $(evt.currentTarget);
      this.$('.selected-direction').text($target.text());
      var directionValue = window.parseInt($target.attr('data-value'), 10);
      this.setDirection(directionValue);

      this.resetAndUpdate();
    },

    changeKeywords: function(evt) {
      var $target = $(evt.currentTarget);
      this.keywords = $target.val();
      this.$('.course-collection').css('opacity', 0.5);

      // TODO(david): Could use jQuery deferreds for this sort of thing
      if (this.timer) {
        // Prevent multiple API searches if entering multiple characters
        window.clearTimeout(this.timer);
      }

      this.timer = window.setTimeout(_.bind(function() {
        this.resetAndUpdate();
      }, this), FETCH_DELAY_MS);
    },

    setDirection: function(direction) {
      var directionName;
      if (direction > 0) {
        directionName = 'ascending';
      } else {
        directionName = 'descending';
      }
      this.direction = {
        'value': direction,
        'name': directionName
      };
    },

    resetCourses: function() {
      this.courses.reset();
      this.hasMore = true;
      this.offset = 0;
    },

    /**
     * Doesn't clear existing courses (just fades them) until new data arrives
     */
    resetAndUpdate: function() {
      this.offset = 0;
      this.hasMore = true;
      this.$('.course-collection').css('opacity', 0.5);
      this.updateCourses(/* reset */ true);
    },

    /**
     * @param {boolean} reset Whether to clear courses before appending new ones
     */
    updateCourses: function(reset) {
      if (!this.hasMore || this.updatingCourses) {
        // TODO(mack): handle case of very short interval between changing
        // search options
        return;
      }
      this.$('.loader').removeClass('hide');
      this.updatingCourses = true;
      // TODO(mack): use $.ajax to handle error
      var args = [];
      args.push('offset=' + this.offset);
      args.push('count=' + this.count);
      if (this.sortMode) {
        args.push('sort_mode=' + this.sortMode.value);
      }
      if (this.direction) {
        args.push('direction=' + this.direction.value);
      }
      if (this.keywords) {
        args.push('keywords=' + this.keywords);
      }
      $.getJSON(
        '/api/course-search?' + args.join('&'),
        _.bind(function(data) {
          if (reset) {
            this.courses.reset();
          }
          var userCourseObjs = data.user_course_objs;
          var courseObjs = data.course_objs;
          var userObjs = data.user_objs;
          var professorObjs = data.professor_objs;

          user.UserCollection.addToCache(userObjs);
          _user_course.UserCourses.addToCache(userCourseObjs);
          _course.CourseCollection.addToCache(courseObjs);
          _prof.ProfCollection.addToCache(professorObjs);

          this.hasMore = data.has_more;
          this.offset += courseObjs.length;

          // TODO(mack): investigate less akward way of doing this
          _.each(courseObjs, function(courseObj) {
            var id = courseObj.id;
            var course = _course.CourseCollection.getFromCache(id);
            this.courses.add(course);
          }, this);

          this.updatingCourses = false;
          this.$('.loader').addClass('hide');
          this.$('.course-collection').css('opacity', 1);
        }, this)
      );
    }
  });

  var init = function() {
    var courseSearchView = new CourseSearchView({});
    $('#course-page-container').append(courseSearchView.render().$el);
  };

  init();
});
