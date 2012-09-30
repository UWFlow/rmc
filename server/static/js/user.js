define(
['rmc_backbone', 'ext/underscore', 'ext/underscore.string', 'util', 'course'],
function(RmcBackbone, _, _s, util, _course) {

  window.UserModel = RmcBackbone.Model.extend({
    defaults: {
      id: '0000000001',
      fbid: 1647810326,
      name: 'Mack Duan',
      last_term_name: 'Spring 2012',
      last_term_course_ids: [],
      // If this user is a friend, mutual_courses will be stored
      // TODO(mack): maybe should have FriendModel as subclass of UserModel
      mutual_course_ids: undefined
    },

    referenceFields: {
      'mutual_courses': ['mutual_course_ids', _course.CourseCollection],
      'last_term_courses': ['last_term_course_ids', _course.CourseCollection]
    },

    initialize: function(attributes) { },

    getFbPicUrl: function() {
      // TODO(mack): add support for custom width and height
      return _s.sprintf(
        'https://graph.facebook.com/%s/picture', this.get('fbid'));
    },

    getProfileUrl: function() {
      return '/profile/' + this.get('id');
    },

    toJSON: function() {
      var json = this._super('toJSON', arguments);
      return _.extend(json, {
        profile_url: this.getProfileUrl(),
        fb_pic_url: this.getFbPicUrl()
      });
    }
  });

  var UserCollection = RmcBackbone.Collection.extend({
    model: UserModel
  });
  UserCollection.registerCache('user');

  // TODO(mack): remove stub data
  UserCollection.getSampleCollection = function() {
    var usersData = [
      {
        id: '001',
        fbid: 541400376,
        name: 'David Hu',
        last_term_name: 'Spring 2012'
      },
      {
        id: '002',
        fbid: 1647810326,
        name: 'Mack Duan',
        last_term_name: 'Fall 2012'
      },
      {
        id: '003',
        fbid: 518430508,
        name: 'Sandy Wu',
        last_term_name: 'Fall 2012'
      },
      {
        id: '004',
        fbid: 709180245,
        name: 'Wen-Hao Lue',
        last_term_name: 'Spring 2012'
      },
      {
        id: '005',
        fbid: 730676205,
        name: 'Zameer Manji',
        last_term_name: 'Fall 2012'
      },
      {
        id: '006',
        fbid: 646460492,
        name: 'Joseph Hong',
        last_term_name: 'Fall 2012'
      },
      {
        id: '007',
        fbid: 511515597,
        name: 'Andy Pincombe',
        last_term_name: 'Winter 2012'
      },
      {
        id: '008',
        fbid: 784910429,
        name: 'Anthony Wong',
        last_term_name: 'Winter 2012'
      },
      {
        id: '009',
        fbid: 1286400131,
        name: 'Vladmir Li',
        last_term_name: 'Winter 2012'
      },
      {
        id: '010',
        fbid: 1652790284,
        name: 'Jamie Wong',
        last_term_name: 'Fall 2012'
      }
    ];

    var num = util.random(0, usersData.length);
    return new UserCollection(util.randomItems(usersData, num));
  };

  return {
    UserModel: UserModel,
    UserCollection: UserCollection
  };
});
