require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'course', 'ext/bootstrap', 'rmc_backbone', 'user', 'user_course', 'course', 'prof', 'sign_in'],
function($, _, _s, course, __, RmcBackbone, user, _user_course, _course, _prof, _sign_in) {

  var FETCH_DELAY_MS = 300;

  user.UserCollection.addToCache(pageData.userObjs);

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
      this.term = window.pageData.terms[0];
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
      this.$el.html(_.template($('#search-form-tpl').html(), {
        terms: pageData.terms,
        sortModes: pageData.sortModes,
        directions: pageData.directions,
        selectedTerm: this.term,
        selectedSortMode: this.sortMode,
        selectedDirection: this.direction
      }));

      var $friendOption = this.$('.sort-mode-dropdown [data-value="friends"]');
      $friendOption.click(function(evt) {
        if (!pageData.currentUserId) {
          _sign_in.renderModal({
            title: 'Oops!',
            message: 'We don\'t know who your friends are...',
            fbConnectText: 'Let us know!',
            source: 'MODAL_FRIENDS_TAKEN'
          });
          return false;
        }
      });

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
      'click .term-dropdown .dropdown-menu li': 'changeTerm',
      'click .sort-mode-dropdown .dropdown-menu li': 'changeSortMode',
      'click .direction-dropdown .dropdown-menu li': 'changeDirection',
      'input .keywords': 'changeKeywords',
      'paste .keywords': 'changeKeywords'
    },

    changeTerm: function(evt) {
      var $target = $(evt.currentTarget);
      this.$('.selected-term').text($target.text());
      this.setTerm($target.attr('data-value'));

      this.resetAndUpdate();
    },

    changeSortMode: function(evt) {
      var $target = $(evt.currentTarget);
      this.$('.selected-sort-mode').text($target.text());
      this.setSortMode($target.attr('data-value'));
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

    setTerm: function(termValue) {
      this.term = _.find(pageData.terms, function(term) {
        return term.value === termValue;
      });
    },

    setSortMode: function(sortValue) {
      this.sortMode = _.find(pageData.sortModes, function(sortMode) {
        return sortValue === sortMode.value;
      }, this);
    },

    setDirection: function(directionValue) {
      this.direction = _.find(pageData.directions, function(direction) {
        return direction.value === directionValue;
      });
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
      var args = {
        offset: this.offset,
        count: this.count,
        term: this.term.value,
        sort_mode: this.sortMode.value,
        direction: this.direction.value,
        keywords: this.keywords
      };

      mixpanel.track('Course search request', args);
      // TODO(mack): use $.ajax to handle error
      $.getJSON(
        '/api/course-search',
        args,
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
    $('#course-search-container').append(courseSearchView.render().$el);

    _sign_in.renderBannerIfNecessary(
        'BANNER_SEARCH_PAGE', 'See what your friends are taking!');
  };

  init();

  mixpanel.track('Impression: Search page');
});
