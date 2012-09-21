require(
['ext/jquery','course', 'took_this', 'user', 'tips'],
function($, course, tookThis, user, tips) {
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

        // TODO(david): Delete stub data
        var tipsData = [{
            userId: '1234',
            name: 'Mack Duan',
            comment: "I don't know..."
          }, {
            userId: '1235',
            name: 'Sandy Wu',
            comment: 'Eat. Sleep. Food!'
          }, {
            userId: '1236',
            name: 'David Hu',
            comment: 'blah balh balh balhb'
        }];
        var tipsCollection = new tips.TipsCollection(tipsData);

        var tipsView = new tips.TipsCollectionView({
          collection: tipsCollection
        });
        $('#tips-collection-placeholder').replaceWith(tipsView.render().el);
      }
    );

  });
});
