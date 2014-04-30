define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'util'],
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
      this.template = _.template($('#sections-collection-tpl').html());
      this.shouldLinkifyProfs = options.shouldLinkifyProfs;
    },

    render: function() {
      var terms = this.collection.groupedByTerm();

      _.each(_.keys(terms).sort(), _.bind(function(termId) {
        this._addTermTable(terms, termId);
        _.each(terms[termId], _.bind(this._addSectionRow, this));
        this.$('.sections-table-body-placeholder').
          removeClass('sections-table-body-placeholder');
      }, this));

      return this;
    },

    _addTermTable: function(terms, termId) {
      this.$el.append(this.template({
        term: terms[termId],
        termName: util.humanizeTermId(termId),
        lastUpdated: moment(terms[termId][0].get('last_updated')).fromNow(),
        courseParts: util.splitCourseId(terms[termId][0].get('course_id')),
        questId: util.termIdToQuestId(termId),
      }));
    },

    _addSectionRow: function(section) {
      this.$('.sections-table-body-placeholder').append(
        new TermView({
        model: section,
        shouldLinkifyProfs: this.shouldLinkifyProfs
      }).render().el);
    }
  });

  var TermView = RmcBackbone.View.extend({
    className: 'term-table',

    tagName: 'tr',

    initialize: function(options) {
      this.template = _.template($('#section-row-tpl').html());
      this.shouldLinkifyProfs = options.shouldLinkifyProfs;
    },

    events: {
      'click .add-course-alert-btn': 'onAlertAdd'
    },

    onAlertAdd: function() {
      // TODO(ryandv): Yay, circular dependencies!
      var _user = require('user');
      console.log(_user);
      $.ajax({
        url: '/api/v1/alerts/course/email',
        type: 'POST',
        data: {
          course_id: this.model.get('course_id'),
          section_type: this.model.get('section_type'),
          section_num: this.model.get('section_num'),
          term_id: this.model.get('term_id'),
          user_id: _user.getCurrentUser().get('id'),
        }})
        .done(onAlertAddSuccess);

      return false;
    },

    onAlertAddSuccess: function() {
    },

    render: function() {
      this.$el.addClass(
        util.sectionTypeToCssClass(this.model.get('section_type')));

      if (this._sectionIsFull(this.model)) {
        this.$el.addClass('full');
      }

      this.$el.append(this.template({
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
