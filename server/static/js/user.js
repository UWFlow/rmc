define(
['ext/backbone', 'ext/underscore', 'ext/underscore.string'],
function(Backbone, _, _s) {

  var UserModel = Backbone.Model.extend({
    defaults: {
      id: '0000000001',
      fbid: 1647810326,
      name: 'Mack Duan',
      lastTermName: 'Spring 2012',
      coursesTook: []
    },

    getFbPicUrl: function() {
      // TODO(mack): add support for custom width and height
      return _s.sprintf(
        'https://graph.facebook.com/%d/picture', this.get('fbid'));
    },

    getProfileUrl: function() {
      return '/profile/' + this.get('id');
    },

    toJSON: function() {
      var json = this._super('toJSON');
      return _.extend(json, {
        profileUrl: this.getProfileUrl(),
        fbPicUrl: this.getFbPicUrl()
      });
    }
  });

  var UserCollection = Backbone.Collection.extend({
    model: UserModel
  });

  return {
    UserModel: UserModel,
    UserCollection: UserCollection
  };
});
