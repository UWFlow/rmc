require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'course', 'ext/bootstrap', 'rmc_backbone', 'user'],
function($, _, _s, course, __, RmcBackbone, user) {

  var CourseSearchView = RmcBackbone.View.extend({
    className: 'course-search',
    timer: undefined,
    keywords: undefined,
    sortMode: undefined,
    direction: undefined,
    count: 10,
    offset: 0,
    courseCollection: undefined,
    hasMore: true,

    initialize: function(options) {
      this.sortMode = window.pageData.sortModes[0];
      this.setDirection(this.sortMode.direction);
      this.courseCollection = new course.CourseCollection();
      $(window).scroll(_.bind(this.scrollWindow, this));
    },

    scrollWindow: function(evt) {
      var loaderOffset = this.$('.loader-container').offset().top;
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
      var courseCollectionView = new course.CourseCollectionView({
        courseCollection: this.courseCollection
      });
      this.$('.course-collection-placeholder').replaceWith(courseCollectionView.render().$el);
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

      this.resetCourses();
      this.updateCourses();
    },

    changeDirection: function(evt) {
      var $target = $(evt.currentTarget);
      this.$('.selected-direction').text($target.text());
      var directionValue = window.parseInt($target.attr('data-value'), 10);
      this.setDirection(directionValue);

      this.resetCourses();
      this.updateCourses();
    },

    changeKeywords: function(evt) {
      var $target = $(evt.currentTarget);
      this.keywords = $target.val();

      if (this.timer) {
        // Prevent multiple API searches if entering multiple characters
        window.clearTimeout(this.timer);
      }

      this.resetCourses();
      this.timer = window.setTimeout(_.bind(this.updateCourses, this), 500);
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
      this.courseCollection.reset();
      this.hasMore = true;
      this.offset = 0;
    },

    updateCourses: function() {
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
          var courses = data.courses;
          this.hasMore = data.has_more;
          this.offset += courses.length;
          this.courseCollection.add(courses);
          this.updatingCourses = false;
          this.$('.loader').addClass('hide');
        }, this)
      );
    }
  });

  var init = function() {
    (function() {
      var courseSearchView = new CourseSearchView({});
      $('#course-page-container').append(courseSearchView.render().$el);
    })();

    (function() {
    })();
  };

  init();
});
