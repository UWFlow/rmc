define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'alert', 'util'],
function(RmcBackbone, $, _, _s, _alert, util) {

  var Section = RmcBackbone.Model.extend({
  });

  var SectionCollection = RmcBackbone.Collection.extend({
    model: Section,

    onReset: function(alerts) {
      this.each(function(section) {
        var alertForSection = alerts.find(function(alert) {
          return alert.get('term_id') === section.get('term_id') &&
            alert.get('section_type') === section.get('section_type') &&
              alert.get('section_num') === section.get('section_num') &&
                alert.get('course_id') === section.get('course_id');
        });

        section.set({ alert: alertForSection });
      });
    },

    initialize: function() {
      this.alerts = new _alert.AlertCollection();
      this.alerts.fetch({reset: true});
      this.alerts.on('reset', this.onReset, this);
    },

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
      this.model.on("change:alert", this.render, this);
    },

    events: {
      'click .add-course-alert-btn': 'onAlertAdd',
      'click .rem-course-alert-btn': 'onAlertRemove',
    },

    onAlertAdd: function() {
      var alert = new _alert.Alert({
        course_id: this.model.get('course_id'),
        section_type: this.model.get('section_type'),
        section_num: this.model.get('section_num'),
        term_id: this.model.get('term_id'),
      });

      this.model.set({ alert: alert });

      alert.save({
        success: _.bind(this.onAlertAddSuccess, this),
        error: _.bind(this.onAlertAddFail, this)
      });

      return false;
    },

    onAlertAddSuccess: function() {
      toastr.success(_s.sprintf("You will be emailed when %s %s %s has open seats.",
                                this.model.get('course_id').toUpperCase(),
                                this.model.get('section_type'),
                                this.model.get('section_num')));
    },

    onAlertAddFail: function() {
      this.model.unset('alert');
      toastr.error(_s.sprintf(
        "Couldn't create an alert for %s %s %s! " +
          "Are you already waiting on this section?",
          this.model.get('course_id').toUpperCase(),
          this.model.get('section_type'),
          this.model.get('section_num')));
    },

    onAlertRemove: function() {
      console.log(this.model.isNew());
      this.model.get('alert').destroy({
        success: _.bind(this.onAlertRemSuccess, this),
        error: _.bind(this.onAlertRemFail, this)
      });
    },

    onAlertRemSuccess: function() {
      toastr.info(_s.sprintf(
        'You will no longer be emailed when ' +
          '%s %s %s has open seats.',
          this.model.get('course_id').toUpperCase(),
          this.model.get('section_type'),
          this.model.get('section_num')));
    },

    onAlertRemFail: function() {
      toastr.error(_s.sprintf(
        'Uh-oh! Something went wrong trying to ' +
          'remove this alert!',
          this.model.get('course_id').toUpperCase(),
          this.model.get('section_type'),
          this.model.get('section_num')));
    },

    render: function() {
      this.$el.empty();
      this.$el.addClass('section-' +
        util.sectionTypeToCssClass(this.model.get('section_type')));

      if (this._sectionIsFull(this.model)) {
        this.$el.addClass('full');
      }

      this.$el.append(this.template({
        section: this.model,

        sectionIsFull: this._sectionIsFull(this.model),

        hasAlert: this.model.has('alert'),

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
