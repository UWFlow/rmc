define(
['rmc_backbone', 'ext/jquery', 'ext/toastr', 'ext/underscore'],
function(RmcBackbone, $, _, toastr) {

  var Alert = RmcBackbone.Model.extend({

    save: function(options) {
      var _user = require('user');
      $.ajax({
        url: '/api/v1/alerts/course/email',
        type: 'POST',
        data: {
          course_id: this.get('course_id'),
          section_type: this.get('section_type'),
          section_num: this.get('section_num'),
          term_id: this.get('term_id'),
          user_id: _user.getCurrentUser().get('id'),
        }})
        .then(options.success, options.error);
    },
  });

  var AlertCollection = RmcBackbone.Collection.extend({
    model: Alert,

    url: '/api/v1/user/alerts',

    initialize: function() {
      this.fetch();
    },

    parse: function(response) {
      return response.alerts;
    },
  });

  return {
    Alert: Alert,
    AlertCollection: AlertCollection,
  };
});
