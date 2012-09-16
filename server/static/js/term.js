define(
['ext/backbone', 'ext/underscore', 'course'],
function(Backbone, _, course) {

  var TermModel = Backbone.Model.extend({
    defaults: {
      'name': 'Fall 2012',
      'courses': new course.CourseCollection()
    },

    idAttribute: 'name'
  });


  var TermView = Backbone.View.extend({
    className: 'term',

    initialize: function(options) {
      this.termModel = options.termModel;
    },

    render: function(options) {
      this.$el.html(
        _.template($('#term-tpl').html(), this.termModel.toJSON()));
      this.courseCollectionView = new course.CourseCollectionView({
        courseCollection: this.termModel.get('courseCollection')
      });
      this.$el.find('.course-collection-placeholder').replaceWith(
        this.courseCollectionView.render().el);
      this.$('.course-collection').addClass('hide-initial');

      return this;
    },

    events: {
      'click .term-name': 'toggleTermVisibility'
    },

    toggleTermVisibility: function(evt) {
      if (this.$('.course-collection').is(':visible')) {
        this.collapseTerm(evt);
      } else {
        this.expandTerm(evt);
      }
    },

    expandTerm: function(evt) {
      var duration = 300;
      this.$('.course-collection')
        .css('opacity', 0)
        .animate({
          opacity: 1.0
        }, {
          duration: duration,
          queue: false
        })
        .slideDown(duration);
    },

    collapseTerm: function(evt) {
      this.$('.course-collection')
        .stop(/* clearQueue */ true)
        .slideUp(300);
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
        var termView = new TermView({
          tagName: 'li',
          termModel: termModel
        });
        this.$el.append(termView.render().el);
        this.termViews.push(termView);
      }, this);

      if (this.termViews) {
        this.termViews[0].toggleTermVisibility();
      }

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
