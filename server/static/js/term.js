define(
['ext/backbone', 'ext/underscore', 'course', 'jquery.slide'],
function(Backbone, _, course, jqSlide) {

  var TermModel = Backbone.Model.extend({
    defaults: {
      'name': 'Fall 2012',
      'program_year_id': '3A',
      'courses': new course.CourseCollection()
    },

    idAttribute: 'name'
  });


  var TermView = Backbone.View.extend({
    className: 'term',

    initialize: function(options) {
      this.termModel = options.termModel;
      this.expand = options.expand;
    },

    render: function(options) {
      var attributes = this.termModel.toJSON();
      attributes.expand = this.expand;
      this.$el.html(
        _.template($('#term-tpl').html(), attributes));
      this.courseCollectionView = new course.CourseCollectionView({
        courseCollection: this.termModel.get('courseCollection')
      });
      this.$el.find('.course-collection-placeholder').replaceWith(
        this.courseCollectionView.render().el);

      if (!this.expand) {
        this.$('.course-collection').addClass('hide-initial');
      }

      return this;
    },

    events: {
      'click .term-name': 'toggleTermVisibility'
    },

    // TODO(mack): remove duplicate with similar logic in CourseView
    toggleTermVisibility: function(evt) {
      if (this.$('.course-collection').is(':visible')) {
        this.collapseTerm(evt);
      } else {
        this.expandTerm(evt);
      }
    },

    expandTerm: function(evt) {
      this.$('.course-collection').fancySlide('down')
        .end().find('.term-name .arrow')
          .removeClass('icon-caret-right')
          .addClass('icon-caret-down');
    },

    collapseTerm: function(evt) {
      this.$('.course-collection').fancySlide('up')
        .end().find('.term-name .arrow')
          .removeClass('icon-caret-down')
          .addClass('icon-caret-right');
    }

  });


  var TermCollection = Backbone.Collection.extend({
    model: TermModel
  });


  var TermCollectionView = Backbone.View.extend({
    tagName: 'ol',
    className: 'term-collection',

    initialize: function(options) {
      this.termCollection = options.termCollection;
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

  return {
    TermModel: TermModel,
    TermView: TermView,
    TermCollection: TermCollection,
    TermCollectionView: TermCollectionView
  };
});
