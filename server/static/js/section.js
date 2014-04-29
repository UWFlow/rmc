define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string', 'util'],
function(RmcBackbone, $, _, _s, util) {

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
      this.sectionCollectionTemplate = _.template($('#sections-collection-tpl').html());
      this.shouldLinkifyProfs = options.shouldLinkifyProfs;
    },

    render: function() {
      var terms = this.collection.groupedByTerm();

      _.each(_.keys(terms).sort(), _.bind(function(termId) {
        this.$el.append(this.sectionCollectionTemplate({
          term: terms[termId],
          termId: termId,
        }));

        _.each(terms[termId], _.bind(function(section) {
          this.$('.sections-table-body-placeholder').append(
            new TermView({
              model: section,
              shouldLinkifyProfs: this.shouldLinkifyProfs
            }).render().el);
        }, this));

        this.$('.sections-table-body-placeholder').removeClass('sections-table-body-placeholder');

      }, this));

      return this;
    }
  });

  var TermView = RmcBackbone.View.extend({
    className: 'term-table',

    tagName: 'tr',

    initialize: function(options) {
      this.sectionRowTemplate = _.template($('#section-row-tpl').html());
      this.shouldLinkifyProfs = options.shouldLinkifyProfs;
    },

    render: function() {
      this.$el.addClass(util.sectionTypeToCssClass(this.model.get('section_type')));

      if (this._sectionIsFull(this.model)) {
        this.$el.addClass('full');
      }

      this.$el.append(this.sectionRowTemplate({
        section: this.model,

        sectionIsFull: this._sectionIsFull(this.model),

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
    },

    _sectionIsFull: function(section) {
      var total = section.get('enrollment_total');
      var cap = section.get('enrollment_capacity');
      return total >= cap;
    },
  });

  return {
    Section: Section,
    SectionCollection: SectionCollection,
    SectionCollectionView: SectionCollectionView
  };
});
