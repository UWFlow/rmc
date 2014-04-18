define(
['rmc_backbone', 'ext/underscore', 'ext/underscore.string', 'util', 'course',
'points'],
function(RmcBackbone, _, _s, util, _course, _points) {

  var getShortProgramName = function(programName) {
    programName = programName || '';
    programName = programName.replace('Mathematics', 'Math');
    programName = programName.replace('Chartered Accountancy', 'CA');
    programName = programName.replace(
        'Accounting and Financial Management', 'AFM');
    programName = programName.replace(/ - .* Option$/, '');

    return programName;
  };

  var UserModel = RmcBackbone.Model.extend({
    defaults: {
      id: '0000000001',
      fbid: 1647810326,
      name: 'Mack Duan',
      last_term_name: 'Spring 2012',
      last_term_course_ids: [],
      friend_ids: [],
      // If this user is a friend, mutual_courses will be stored
      // TODO(mack): maybe should have FriendModel as subclass of UserModel
      mutual_course_ids: [],
      course_history: [],
      num_invites: null,
      num_points: null
    },

    referenceFields: function() {
      return {
        'mutual_courses': ['mutual_course_ids', _course.CourseCollection],
        'last_term_courses': ['last_term_course_ids', _course.CourseCollection],
        'friends': ['friend_ids', UserCollection]
      };
    },

    initialize: function(attributes) { },

    getProfileUrl: function() {
      return '/profile/' + this.get('id');
    },

    getShortProgramName: function() {
      var programName = this.get('program_name');
      return getShortProgramName(programName);
    },

    toJSON: function() {
      var json = this._super('toJSON', arguments);
      return _.extend(json, {
        profile_url: this.getProfileUrl(),
        profile_pic_urls: this.get('profile_pic_urls'),
        short_program_name: this.getShortProgramName()
      });
    },

    gainPoints: function(numPoints) {
      if (numPoints <= 0) {
        return;
      }
      this.set('num_points', this.get('num_points') + numPoints);
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

  var getCurrentUser = function() {
    // TODO(david): Cache this
    if (window.pageData.currentUserId) {
      return UserCollection.getFromCache(window.pageData.currentUserId.$oid);
    }
    return null;
  };

  return {
    UserModel: UserModel,
    UserCollection: UserCollection,
    getShortProgramName: getShortProgramName,
    getCurrentUser: getCurrentUser
  };
});
