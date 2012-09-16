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
        this.sortMode = window.pageData.sortModes[0];
        this.setDirection(this.sortMode.direction);
      },

      render: function() {
        console.log('dir', this.direction);
        console.log('sort', this.sortMode);
        var sortModes = window.pageData.sortModes;
        this.$el.html(_.template($('#search-form-tpl').html(), {
          sortModes: sortModes,
          selectedSortMode: this.sortMode,
          selectedDirection: this.direction
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
        var sortValue = $target.attr('data-value');
        this.sortMode = _.find(window.pageData.sortModes, function(sortMode) {
          return sortValue === sortMode.value;
        }, this);
        this.setDirection(this.sortMode.direction);
        this.$('.selected-direction').text(this.direction.name);
        this.updateCourses();
      },

      changeDirection: function(evt) {
        var $target = $(evt.currentTarget);
        this.$('.selected-direction').text($target.text());
        var directionValue = window.parseInt($target.attr('data-value'), 10);
        this.setDirection(directionValue);
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

      setDirection: function(direction) {
        var directionName = undefined;
        if (direction > 0) {
          directionName = 'ascending';
        } else {
          directionName = 'descending';
        }
        this.direction = {
          'value': direction,
          'name': directionName
        }
      },

      updateCourses: function() {
        console.log('1dir', this.direction);
        console.log('1sort', this.sortMode);
        // TODO(mack): use $.ajax to handle error
        var args = [];
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
