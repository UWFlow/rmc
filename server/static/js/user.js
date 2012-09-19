define(
['ext/backbone', 'ext/underscore', 'ext/underscore.string', 'util'],
function(Backbone, _, _s, util) {

  var UserModel = Backbone.Model.extend({
    defaults: {
      id: '0000000001',
      fbid: 1647810326,
      name: 'Mack Duan',
      lastTermName: 'Spring 2012',
      // TODO(mack): should be CourseCollection rather than array
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

  // TODO(mack): remove stub data
  UserCollection.getSampleCollection = function() {
    var usersData = [
      {
        id: '001',
        fbid: 541400376,
        name: 'David Hu',
        lastTermName: 'Spring 2012',
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
      {
        id: '004',
        fbid: 709180245,
        name: 'Wen-Hao Lue',
        lastTermName: 'Spring 2012',
        coursesTook: [],
      },
      {
        id: '005',
        fbid: 730676205,
        name: 'Zameer Manji',
        lastTermName: 'Fall 2012',
        coursesTook: []
      },
      {
        id: '006',
        fbid: 646460492,
        name: 'Joseph Hong',
        lastTermName: 'Fall 2012',
        coursesTook: []
      }
    ];

    var num = util.random(0, usersData.length);
    return new UserCollection(util.randomItems(usersData, num));
  }

  return {
    UserModel: UserModel,
    UserCollection: UserCollection
  };
});
