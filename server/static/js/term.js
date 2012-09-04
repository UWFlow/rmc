define(
['ext/backbone', 'ext/underscore', 'course'],
function(Backbone, _, course) {

  var TermModel = Backbone.Model.extend({
    defaults: {
      'name': 'Fall 2012',
      'courses': new course.CourseModel()
    }
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

      return this;
    },

    events: {
      'click .term-name': 'toggleTermVisibility'
    },

    toggleTermVisibility: function(evt) {
      this.$('.course-collection').toggle();
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
      this.termCollection.each(function(termModel) {
        var termView = new TermView({
          tagName: 'li',
          termModel: termModel
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
