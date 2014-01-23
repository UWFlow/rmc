define(
['rmc_backbone', 'ext/underscore', 'ext/jquery', 'course', 'jquery.slide',
 'user_course', 'util', 'work_queue'],
function(RmcBackbone, _, $, _course, jqSlide, _user_course, _util) {

  var TermModel = RmcBackbone.Model.extend({
    defaults: {
      'id': '2012_09',
      'name': 'Fall 2012',
      'program_year_id': '3A',
      'course_ids': []
    },

    referenceFields: {
      'courses': ['course_ids', _course.CourseCollection]
    }
  });


  var TermView = RmcBackbone.View.extend({
    className: 'term',

    initialize: function(options) {
      this.termModel = options.termModel;
      this.courses = this.termModel.get('courses');

      this.courseCollectionView = new _course.CourseCollectionView({
        courses: this.courses,
        canShowAddReview: pageData.ownProfile
      });

      var savedExpanded = _util.getLocalData(this.getTermExpandedKey());
      this.expand = savedExpanded == null ? options.expand : savedExpanded;
      this.hasBeenExpanded = false;
    },

    render: function(options) {
      var attributes = this.termModel.toJSON();
      attributes.expand = this.expand;

      this.$el.html(
        _.template($('#term-tpl').html(), attributes));

      if (this.expand && !this.hasBeenExpanded) {
        this.hasBeenExpanded = true;
        this.$el.find('.course-collection-placeholder').replaceWith(
          this.courseCollectionView.render().el);
      }

      if (!this.expand) {
        this.$('.course-collection').addClass('hide-initial');
      }

      return this;
    },

    getTermExpandedKey: function() {
      return 'termExpanded:' + this.termModel.get('id');
    },

    events: {
      'click .term-name': 'toggleTermVisibility',
      'expand': 'expandTerm'
    },

    // TODO(mack): remove duplicate with similar logic in CourseView
    toggleTermVisibility: function(evt) {
      var termVisible = this.$('.course-collection').is(':visible');
      if (termVisible) {
        this.collapseTerm(evt);
      } else {
        this.expandTerm(evt);
      }
      _util.storeLocalData(this.getTermExpandedKey(), !termVisible);
    },

    expandTerm: function(evt) {
      if (!this.hasBeenExpanded) {
        this.expand = true;
        this.render();
      }

      this.$('.course-collection').fancySlide('down')
        .end().find('.term-name .arrow')
          .removeClass('icon-caret-right')
          .addClass('icon-caret-down');
      // TODO(david): Make this fn automatically called on show of courses
      this.courseCollectionView.onShow();
    },

    collapseTerm: function(evt) {
      this.expand = false;

      this.$('.course-collection').fancySlide('up')
        .end().find('.term-name .arrow')
          .removeClass('icon-caret-down')
          .addClass('icon-caret-right');
    }

  });


  var TermCollection = RmcBackbone.Collection.extend({
    model: TermModel
  });


  var TermCollectionView = RmcBackbone.View.extend({
    tagName: 'ol',
    className: 'term-collection',

    initialize: function(attributes) {
      this.termCollection = attributes.termCollection;
      this.termViews = [];
    },

    render: function() {
      this.$el.empty();
      this.termCollection.each(function(termModel, idx) {
        var expand = idx < 3;
        var termView = new TermView({
          tagName: 'li',
          termModel: termModel,
          expand: expand
        });
        this.$el.append(termView.render().el);
        this.termViews.push(termView);
      }, this);

      return this;
    }
  });

  var AddTermBtnView = RmcBackbone.View.extend({
    className: 'add-term-btn',

    initialize: function() {
      this.template = _.template($('#add-term-btn-tpl').html());
    },

    render: function() {
      this.$el.html(this.template({}));
      return this;
    },

    events: {
      'click': 'onAddTermBtnClick'
    },

    onAddTermBtnClick: function() {
      $('.schedule-input-modal').modal();  // TODO(david): This is a hack
    }
  });

  var ProfileTermsView = RmcBackbone.View.extend({
    className: 'profile-terms',
    initialize: function(options) {
      this.termCollection = options.termCollection;
      this.termCollectionView = new TermCollectionView({
        termCollection: this.termCollection
      });
      if (options.showAddTerm) {
        this.addTermBtnView = new AddTermBtnView();
      }

      this.template = _.template($('#profile-terms-tpl').html());
    },

    events: {
      'autoScroll': 'scrollToNextCourseDelayed'
    },

    scrollToNextCourseDelayed: function(event, course) {
      setTimeout(_.bind(this.scrollToNextCourse, this, event, course), 400);
    },

    scrollToNextCourse: function(event, course) {
      // Get the list of courses, in displayed order, after the current course
      var courses = this.termCollection.reduce(function(list, term) {
        return list.concat(term.get('courses').models);
      }, []);
      var remainingCourses = _.rest(courses, _.indexOf(courses, course) + 1);

      // Find the first non-filled-in course (to scroll to)
      var targetCourse = _.find(remainingCourses, function(remCourse) {
        return !remCourse.get('user_course').isMostlyFilledIn();
      });
      if (!targetCourse) {
        return;
      }

      // Expand the course card
      var userCourseId = targetCourse.get('user_course').get('id');
      $('#' + 'course-view-' + userCourseId).trigger('expand');

      // Scroll!
      _util.scrollToElementId(userCourseId);

      mixpanel.track('Reviewing: Auto scroll', { course_id: course.get('id') });
    },

    render: function() {
      this.$el.html(this.template({}));
      if (this.addTermBtnView) {
        this.$('.add-term-btn-placeholder')
            .replaceWith(this.addTermBtnView.render().el);
      }
      this.$('.term-collection-placeholder')
          .replaceWith(this.termCollectionView.render().el);
      return this;
    }
  });

  return {
    TermModel: TermModel,
    TermView: TermView,
    TermCollection: TermCollection,
    TermCollectionView: TermCollectionView,
    ProfileTermsView: ProfileTermsView
  };
});
