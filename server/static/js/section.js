define(
['rmc_backbone', 'ext/jquery', 'ext/underscore'],
function(RmcBackbone, $, _) {

  var Section = RmcBackbone.Model.extend({
    referenceFields: function() {
      // TODO(david): Resolve circular dependency.
      var _course = require('course');
      return {
       course: ['course_id', _course.CourseCollection]
      };
    },

    getCourseCode: function() {
      var course = this.get('course');
      return course ? course.get('code') : this.get('course_id');
    }
  });

  var SectionCollection = RmcBackbone.Collection.extend({
    model: Section,

    comparator: function(section) {
      return section.get('section_type') + section.get('section_num');
    },

    groupedByTerm: function() {
      return this.chain()
        .groupBy(function(section) { return section.get('term_id'); })
        //.sortBy(function(exams) { return exams[0].get('start_date'); })
        .value();
    }
  });

  var SectionCollectionView = RmcBackbone.View.extend({
    className: 'sections-collection',

    initialize: function() {
      this.template = _.template($('#sections-collection-tpl').html());
    },

    render: function() {
      this.$el.html(this.template({
        terms: this.collection.groupedByTerm()
      }));
      return this;
    }
  });

  return {
    Section: Section,
    SectionCollection: SectionCollection,
    SectionCollectionView: SectionCollectionView
  };
});
