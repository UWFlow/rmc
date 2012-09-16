require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'course', 'ext/bootstrap', 'ext/backbone'],
function($, _, _s, course, _b, Backbone) {
  $(function() {

    var SearchFormView = Backbone.View.extend({
      tagName: 'form',
      className: 'nav nav-pills',
      timer: undefined,
      courseCollectionView: undefined,
      keywords: undefined,
      sortMode: undefined,
      direction: undefined,

      initialize: function(options) {
      },

      render: function() {
        var sortModes = window.pageData.sortModes;
        var directions = window.pageData.directions;
        this.$el.html(_.template($('#search-form-tpl').html(), {
          sortModes: sortModes,
          directions: directions,
          selectedSortMode: sortModes[0],
          selectedDirection: directions[1]
        }));
        $('.dropdown-toggle').dropdown();
        this.updateCourses();

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
        this.sortMode = $target.attr('data-value');
        this.updateCourses();
      },

      changeDirection: function(evt) {
        var $target = $(evt.currentTarget);
        this.$('.selected-direction').text($target.text());
        this.direction = $target.attr('data-value');
        this.updateCourses();
      },

      changeKeywords: function(evt) {
        var $target = $(evt.currentTarget);
        this.keywords = $target.val();

        if (this.timer) {
          // Prevent multiple API searches if entering multiple characters
          window.clearTimeout(this.timer);
        }

        this.timer = window.setTimeout(_.bind(this.updateCourses, this), 500);
      },

      updateCourses: function() {
        // TODO(mack): use $.ajax to handle error
        var args = [];
        if (this.sortMode) {
          args.push('sort_mode=' + this.sortMode);
        }
        if (this.direction) {
          args.push('direction=' + this.direction);
        }
        if (this.keywords) {
          args.push('keywords=' + this.keywords);
        }
        $.getJSON(
          '/api/course-search?' + args.join('&'),
          _.bind(function(data) {
            var courses = data.courses;
            if (this.courseCollectionView) {
              this.courseCollectionView.remove();
              this.courseCollectionView.unbind();
            }
            var courseCollection = new course.CourseCollection(courses);
            this.courseCollectionView = new course.CourseCollectionView({
              courseCollection: courseCollection
            });
            // TODO(mack): make this clear than modifying global id
            $('#courses-container').append(this.courseCollectionView.render().$el);
          }, this)
        );
      }
    });

    var init = function() {
      (function() {
        var searchFormView = new SearchFormView({});
        $('#search-form-container').append(searchFormView.render().$el);
      })();

      (function() {
      })();
    };

    init();
  });
});
