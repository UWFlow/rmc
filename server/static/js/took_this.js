define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ext/underscore.string',
'ext/bootstrap'],
function(RmcBackbone, $, _, _s, bootstrap) {

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

  TookThisSidebarView = RmcBackbone.View.extend({
    className: 'took-this-sidebar',

    initialize: function(attributes) {
      this.collection = attributes.courseCode;
      this.userCourses = attributes.userCourses;
    },

    render: function() {
      this.$el.html(_.template($('#took-this-sidebar-tpl').html(), {
        num_friends: this.userCourses.length,
        course_code: this.courseCode
      }));
      var collectionView = new UserCollectionView({
        collection: this.userCourses
      });
      this.$('.took-this-collection-placeholder').replaceWith(
        collectionView.render().$el);

      return this;
    }
  });

  return {
    TookThisView: TookThisView,
    TookThisSidebarView: TookThisSidebarView
  };
});
