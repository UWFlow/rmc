require(
['ext/jquery', 'ext/underscore', 'course', 'took_this', 'user'],
function($, _, course, tookThis, user) {
  $(function() {

    // TODO(david): Customize with people who took this course.
    courseIds = ['CS137', 'SCI238', 'CS241'];
    $.getJSON(
      '/api/courses/' + courseIds.join(','),
      function(data) {
        var userCollection = user.UserCollection.getSampleCollection();
        var tookThisSidebarView = new tookThis.TookThisSidebarView({
          collection: userCollection
        });
        $('#took-this-sidebar-container').html(tookThisSidebarView.render().el);
      }
    );

  });
});
