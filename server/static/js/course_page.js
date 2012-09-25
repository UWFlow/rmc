require(
['ext/jquery','course', 'took_this', 'user', 'tips', 'prof', 'ratings',
'course'],
function($, course, tookThis, user, tips, prof, ratings) {
  // TODO(david): Customize with people who took this course.
  courseIds = ['CS137', 'SCI238', 'CS241'];

  var courseData = window.pageData.data;
  var courseModel = new course.CourseModel(courseData);
  console.log(courseData);

  var ratingBoxView = new ratings.RatingBoxView({
    model: new ratings.RatingModel(courseData.overall)
  });
  $('#rating-box-container').html(ratingBoxView.render().el);

  var courseInnerView = new course.CourseInnerView({
    courseModel: courseModel
  });
  $('#course-inner-placeholder').html(courseInnerView.render().el);
  courseInnerView.animateBars();

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

  // TODO(david): Handle no professors for course
  var profsCollection = new prof.ProfCollection(courseData.professors);
  var profsView = new prof.ProfCollectionView({ collection: profsCollection });
  $('#professor-review-container').html(profsView.render().el);

});
