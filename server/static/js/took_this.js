define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap', 'util'],
function(RmcBackbone, $, _, _s, bootstrap, util) {

  // TODO(david): Sorry about the terrible name of everything... I'm tired

  var TookThisView = RmcBackbone.View.extend({
    className: 'took-this',

    initialize: function(attributes) {
      this.userCourse = attributes.userCourse;
    },

    render: function() {
      this.$el.html(_.template($('#took-this-tpl').html(), {
        user_course: this.userCourse.toJSON(),
        friend: this.userCourse.get('user').toJSON()
      }));
      return this;
    }
  });

  var UserCollectionView = RmcBackbone.CollectionView.extend({
    className: 'took-this-collection',

    createItemView: function(userCourse) {
      return new TookThisView({ userCourse: userCourse });
    }
  });

  var TookThisSidebarView = RmcBackbone.View.extend({
    className: 'took-this-sidebar',

    initialize: function(attributes) {
      var currentTermId = attributes.currentTermId;
      var userCourses = attributes.userCourses;
      var pastTermUserCourses = new RmcBackbone.Collection();
      var currentTermUserCourses = new RmcBackbone.Collection();
      var futureTermUserCourses = new RmcBackbone.Collection();

      // Sort friend who've taken the course descendingly
      pastTermUserCourses.comparator = function(uc1, uc2) {
        return util.userCourseTermIdComparator(uc1, uc2) * -1;
      };
      // Sort friend who are planning to take the course ascendingly
      futureTermUserCourses.comparator =
        util.userCourseTermIdComparator;

      if (userCourses) {
        // Bucket friends by term taken
        userCourses.each(function(user_course) {
          if (user_course.get('term_id') < currentTermId) {
            pastTermUserCourses.add(user_course);
          } else if (user_course.get('term_id') > currentTermId) {
            futureTermUserCourses.add(user_course);
          } else {
            currentTermUserCourses.add(user_course);
          }
        });
      }

      this.collection = attributes.courseCode;
      this.pastTermUserCourses = pastTermUserCourses;
      this.currentTermUserCourses = currentTermUserCourses;
      this.futureTermUserCourses = futureTermUserCourses;
      this.currentTermId = currentTermId;
    },

    render: function() {
      this.$el.html(_.template($('#took-this-sidebar-tpl').html(), {
        num_friends_past: this.pastTermUserCourses.length,
        num_friends_current: this.currentTermUserCourses.length,
        num_friends_future: this.futureTermUserCourses.length,
        course_code: this.courseCode
      }));
      var pastTermCollectionView = new UserCollectionView({
        collection: this.pastTermUserCourses
      });
      var currentTermCollectionView = new UserCollectionView({
        collection: this.currentTermUserCourses
      });
      var futureTermCollectionView = new UserCollectionView({
        collection: this.futureTermUserCourses
      });
      this.$('.took-this-past-term-collection-placeholder').replaceWith(
        pastTermCollectionView.render().$el);
      this.$('.took-this-current-term-collection-placeholder').replaceWith(
        currentTermCollectionView.render().$el);
      this.$('.took-this-future-term-collection-placeholder').replaceWith(
        futureTermCollectionView.render().$el);

      return this;
    }
  });

  return {
    TookThisView: TookThisView,
    TookThisSidebarView: TookThisSidebarView
  };
});
