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

  UserCollection.getSampleCollection = function() {
    var userCollection = new UserCollection();
    // TODO(mack): remove stub data
    var usersData = [
      {
        id: '001',
        fbid: 541400376,
        name: 'David Hu',
        lastTermName: 'Spring 2012',
        // TODO(mack): should be CourseCollection rather than array
        coursesTook: [],
      },
      {
        id: '002',
        fbid: 164710326,
        name: 'Mack Duan',
        lastTermName: 'Fall 2012',
        coursesTook: []
      },
      {
        id: '003',
        fbid: 518430508,
        name: 'Sandy Wu',
        lastTermName: 'Fall 2012',
        coursesTook: []
      },
    ]
    _.each(usersData, function(userData) {
      var userModel = new UserModel(userData);
      userCollection.add(userModel);
    });

    return userCollection;
  }

  return {
    UserModel: UserModel,
    UserCollection: UserCollection
  };
});
