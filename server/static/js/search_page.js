define(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'course', 'ext/bootstrap', 'rmc_backbone', 'user', 'user_course', 'course', 'prof', 'sign_in'],
function($, _, _s, course, __, RmcBackbone, user, _user_course, _course, _prof, _sign_in) {

  var FETCH_DELAY_MS = 300;

  var CourseSearchView = RmcBackbone.View.extend({
    className: 'course-search',
    timer: undefined,
    keywords: undefined,
    sortMode: undefined,
    count: 10,
    offset: 0,
    courses: undefined,
    hasMore: true,

    initialize: function(options) {
      this.term = window.pageData.terms[0];
      this.sortMode = window.pageData.sortModes[0];
      this.courses = new _course.CourseCollection();
      this.excludeTakenCourses = false;
      $(window).scroll(_.bind(this.scrollWindow, this));
    },

    getIconForMode: function(name) {
      return {
        'popular': 'icon-signal',
        'friends taken': 'icon-group',
        'interesting': 'icon-heart',
        'easy': 'icon-gift',
        'hard': 'icon-warning-sign',
        'course code': 'icon-list-ol'
      }[name];
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
        selectedTerm: this.term,
        selectedSortMode: this.sortMode,
        getIconForMode: this.getIconForMode,
        excludeTakenCourses: this.excludeTakenCourses
      }));

      var $friendOption = this.$('.sort-options [data-value="friends taken"]');
      $friendOption.click(function(evt) {
        if (!pageData.currentUserId) {
          _sign_in.renderModal({
            title: 'Oops!',
            message: 'We don\'t know who your friends are...',
            fbConnectText: 'Let us know!',
            source: 'MODAL_FRIENDS_TAKEN',
            nextUrl: window.location.href
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
      'click .excluding-taken-courses-dropdown .dropdown-menu li': 'changeExcludeTakenCourses',
      'click .term-dropdown .dropdown-menu li': 'changeTerm',
      'click .sort-options .option': 'changeSortMode',
      'input .keywords': 'changeKeywords',
      'paste .keywords': 'changeKeywords'
    },

    changeTerm: function(evt) {
      evt.preventDefault();

      var $target = $(evt.currentTarget);
      this.$('.selected-term').text($target.text());
      this.setTerm($target.attr('data-value'));

      this.resetAndUpdate();
    },

    changeExcludeTakenCourses: function(evt) {
      evt.preventDefault();

      if (!pageData.currentUserId) {
        _sign_in.renderModal({
          title: 'Oops!',
          message: 'We don\'t know which courses you\'ve taken...',
          fbConnectText: 'Let us know!',
          source: 'MODAL_COURSES_TAKEN',
          nextUrl: window.location.href
        });
        return;
      }

      var $target = $(evt.currentTarget);
      this.$('.selected-exclude-option').text($target.text());
      this.setExcludeTakenCourses($target.attr('data-value'));

      this.resetAndUpdate();
    },

    changeSortMode: function(evt) {
      evt.preventDefault();

      var $target = $(evt.currentTarget);
      this.$('.selected-sort-mode').text($target.text());
      this.setSortMode($target.attr('data-value'));
      $target
        .siblings()
          .removeClass('active')
        .end()
        .addClass('active');

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

    setExcludeTakenCourses: function(excludeTakenCourses) {
      this.excludeTakenCourses = excludeTakenCourses;
    },

    setSortMode: function(sortName) {
      this.sortMode = _.find(pageData.sortModes, function(sortMode) {
        return sortName === sortMode.name;
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
        name: this.sortMode.name,
        sort_mode: this.sortMode.value,
        keywords: this.keywords,
        exclude_taken_courses: this.excludeTakenCourses
      };

      mixpanel.track('Course search request', args);
      mixpanel.people.increment({'Course search request': 1});
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

    if (!window.pageData.currentUserId) {
      _sign_in.renderBanner({
        fbConnectText: 'See what your friends are taking!',
        source: 'BANNER_SEARCH_PAGE',
        nextUrl: window.location.href
      });
    }
  };

  init();

  mixpanel.track('Impression: Search page');
});
