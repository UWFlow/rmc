define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string'],
function(RmcBackbone, $, _, _s) {

  var Section = RmcBackbone.Model.extend({
  });

  var SectionCollection = RmcBackbone.Collection.extend({
    model: Section,

    comparator: function(section) {
      var type = section.get('section_type');
      var sectionName = type + section.get('section_num');

      // Ensure lectures are displayed first.
      if (type === 'LEC') {
        return ' ' + sectionName;
      } else {
        return sectionName;
      }
    },

    groupedByTerm: function() {
      return this.groupBy(function(section) {
        return section.get('term_id');
      });
    }
  });

  var SectionCollectionView = RmcBackbone.View.extend({
    className: 'sections-collection',

    initialize: function(options) {
      this.template = _.template($('#sections-collection-tpl').html());
      this.shouldLinkifyProfs = options.shouldLinkifyProfs;
    },

    render: function() {
      this.$el.html(this.template({
        terms: this.collection.groupedByTerm(),
        sectionFullCssClass: function(section) {
          var total = section.get('enrollment_total');
          var cap = section.get('enrollment_capacity');
          return total >= cap ? 'full' : '';
        },
        sectionMissingValueText: function(section, courseId) {
          if (_s.startsWith(courseId, 'wkrpt')) {
            return 'N/A';
          }
          // ONLN ONLINE
          // ONLNG ONLINE
          // ONLNP ONLINE
          // ONLNJ ONLINE
          // ONLNR ONLINE
          var onlinePattern = /ONLN.? ONLINE/;
          return onlinePattern.test(section.get('campus')) ? 'N/A' : 'TBA';
        },
        shouldLinkifyProfs: this.shouldLinkifyProfs
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
