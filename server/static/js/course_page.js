require(
['ext/jquery','course', 'took_this', 'user', 'tips', 'prof', 'ratings'],
function($, course, tookThis, user, tips, prof, ratings) {
  // TODO(david): Customize with people who took this course.
  courseIds = ['CS137', 'SCI238', 'CS241'];
  $.getJSON(
    '/api/courses/' + courseIds.join(','),
    function(data) {
      // TODO(david): Replace mock data
      var ratingBoxView = new ratings.RatingBoxView({
        model: new ratings.RatingModel()
      });
      $('#rating-box-container').html(ratingBoxView.render().el);

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
        }, {
          userId: '1236',
          name: 'Mr. Bean',
          comment: 'Teddy!'
        }, {
          userId: '1237',
          name: 'Sal Khan',
          comment: 'In the town where I was born, lived a man who sailed to sea. And he told us of his life, in the land of submarines. So we sailed on to the sun, till we found a sea of green. And we lived beneath the waves in our yellow submarine.'
      }];
      var tipsCollection = new tips.TipsCollection(tipsData);

      var tipsView = new tips.ExpandableTipsView({ tips: tipsCollection });
      $('#tips-collection-placeholder').replaceWith(tipsView.render().el);

      var profModel = new prof.Prof();
      var profReviews = [{
        name: 'Larry Smith',
        passion: 5,
        clarity: 3,
        overall: 6,
        comment: 'Was great!!!!!!!!!!!!!!!!'
      }, {
        name: 'Charles Clarke',
        passion: 4,
        clarity: 5,
        overall: null,
        comment: 'Great lecturer overall. Funny and casual. blah blah blah'
      }, {
        name: 'Andrew Morton',
        passion: 2,
        clarity: 4,
        overall: null,
        comment: 'Really easy going and cool guy. Really easy going and cool guy. Really easy going and cool guy. Really easy going and cool guy. Really easy going and cool guy. Really easy going and cool guy. Really easy going and cool guy. Really easy going and cool guy. Really easy going and cool guy. Really easy going and cool guy. '
      }];
      var profReviewsCollection = new prof.ProfReviewCollection(profReviews);

      var profView = new prof.ExpandableProfView({
        reviews: profReviewsCollection,
        prof: profModel
      });
      $('#professor-review-container').html(profView.render().el);
    }
  );

});
