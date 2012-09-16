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
        .slideDown(duration, _.bind(function() {
          this.$('.term-name .arrow')
            .removeClass('icon-chevron-down')
            .addClass('icon-chevron-up');
        }, this));
    },

    collapseTerm: function(evt) {
      this.$('.course-collection')
        .stop(/* clearQueue */ true)
        .slideUp(300, _.bind(function() {
          this.$('.term-name .arrow')
            .removeClass('icon-chevron-up')
            .addClass('icon-chevron-down');
        }, this));
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
