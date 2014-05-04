define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/toastr'],
function(RmcBackbone, $, _, _s, toastr) {

  var Alert = RmcBackbone.Model.extend({
    urlRoot: '/api/v1/alerts/course/email',

    initialize: function() {
      var _user = require('user');
      this.set({ user_id: _user.getCurrentUser().get('id') });
    },

    parse: function(data) {
      return {
        id: data.id,
        course_id: data.course_id,
        section_type: data.section_type,
        section_num: data.section_num,
        term_id: data.term_id,
        user_id: data.id
      };
    },
  });

  var AlertView = RmcBackbone.View.extend({
    tagName: 'span',

    events: {
      'click': 'onClick',
    },

    initialize: function() {
      this.model.on('destroy', this.removeId, this);
    },

    removeId: function() {
      this.model.unset('id');
    },

    onClick: function() {
      if (this.model.isNew()) {
        this.onAlertAdd();
      } else {
        this.onAlertRemove();
      }
    },

    onAlertAdd: function() {
      this.model.save({}, {
        success: _.bind(this.onAlertAddSuccess, this),
        error: _.bind(this.onAlertAddFail, this)
      });
      return false;
    },

    onAlertAddSuccess: function() {
      this.render();
      toastr.success(_s.sprintf("You will be emailed when %s %s %s " +
                                "has open seats.",
                                this.model.get('course_id').toUpperCase(),
                                this.model.get('section_type'),
                                this.model.get('section_num')));
    },

    onAlertAddFail: function() {
      toastr.error(_s.sprintf(
        "Couldn't create an alert for %s %s %s! " +
          "Are you already waiting on this section?",
          this.model.get('course_id').toUpperCase(),
          this.model.get('section_type'),
          this.model.get('section_num')));
    },

    onAlertRemove: function() {
      this.model.destroy({
        success: _.bind(this.onAlertRemSuccess, this),
        error: _.bind(this.onAlertRemFail, this)
      });
    },

    onAlertRemSuccess: function() {
      this.render();
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
      this.$el.removeClass();
      this.$el.addClass(this.model.isNew() ?
        'add-course-alert-btn icon-bell' : 'rem-course-alert-btn icon-remove');
      return this;
    }

  });

  var AlertCollection = RmcBackbone.Collection.extend({
    model: Alert,

    url: '/api/v1/user/alerts',

    parse: function(response) {
      return response.alerts;
    },
  });

  return {
    Alert: Alert,
    AlertView: AlertView,
    AlertCollection: AlertCollection,
  };
});
