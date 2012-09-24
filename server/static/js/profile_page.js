require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'transcript',
'term', 'course', 'friend', 'util', 'user'],
function($, _, _s, transcript, term, course, friend, util, user) {

  // Render friend sidebar

  // TODO(mack): remove stub data
  courseIds = ['cs137', 'sci238', 'cs241'];
  $.getJSON(
    '/api/courses/' + courseIds.join(','),
    function(data) {
      var userCollection = user.UserCollection.getSampleCollection();
      var courses = _.toArray(data.courses);
      userCollection.each(function(userModel) {
        var collection = new course.CourseCollection(courses)
        userModel.set('coursesTook', collection);
      });
      var friendSidebarView = new friend.FriendSidebarView({
        friendCollection: userCollection
      });
      $('#friend-sidebar-container').html(friendSidebarView.render().el);
    }
  );

  // Render the transcript, if available
  if (window.pageData.transcriptData) {
    var termCollection = new term.TermCollection();

    _.each(window.pageData.transcriptData, function(termData) {
      var termModel = new term.TermModel({
        name: termData.term_name,
        courseCollection: new course.CourseCollection(termData.course_models)
      });
      termCollection.add(termModel);
    });

    // Add the parsed term and course info to the page for live preview
    var termCollectionView = new term.TermCollectionView({
      termCollection: termCollection
    });
    $('#term-collection-container').html(termCollectionView.render().el);
  }

  var $transcript = $('#transcript-text');

  $transcript.bind('input paste', function(evt) {
    // Remove any old info from the page
    $('#terms').empty();
    $('#transcript-error').empty();

    // Store the transcript text
    var data = $(evt.currentTarget).val();
    if (!data) {
      // If the text area has been emptied, exit immediately w/o
      // showing error message for parse failure.
      return;
    }

    addTranscriptData(data);
  });

  var addTranscriptData = function(data) {
    // Try/catch around parsing logic so that we show error message
    // should anything go wrong
    try {
      coursesByTerm = transcript.parseTranscript(data);
    } catch (ex) {
      $('#transcript-error').text(
          'Could not extract course information. ' +
          'Please check that you\'ve pasted the transcript correctly.');
      return;
    }

    // TODO(mack): fix confusing names between term/termObj and course/courseObj
    var courseIds = [];
    _.each(coursesByTerm, function(termObj) {
      _.each(termObj.courseIds, function(courseId) {
        courseIds.push(courseId);
      });
    });

    $.post(
      '/api/transcript',
      { 'courses_by_term': JSON.stringify(coursesByTerm) },
      function(data) {
        // TODO(Sandy): Logic for rendering the termCollectionView here (move
        // the stuff from below up here)
      },
      'json');

    $.getJSON(
      '/api/courses/' + courseIds.join(','),
      function(data) {
        var courseById = data.courses;

        var termCollection = new term.TermCollection();

        _.each(coursesByTerm, function(termObj) {
          var courseCollection = new course.CourseCollection();
          _.each(termObj.courseIds, function(courseId) {
            if (courseId in courseById) {
              courseCollection.add(courseById[courseId]);
            }
          });
          var termModel = new term.TermModel({
            name: termObj.name,
            courseCollection: courseCollection
          });
          termCollection.add(termModel);
        });

        // Add the parsed term and course info to the page for live preview
        var termCollectionView = new term.TermCollectionView({
          termCollection: termCollection
        });
        $('#term-collection-container').html(termCollectionView.render().el);
      }
    );
  };

  // Handle the case that the user inputs into the transcript text area
  // before the page has finished loading.
  if ($transcript.val()) {
    $transcript.trigger('input');
  }

  var init = function() {
    if (util.getQueryParam('test')) {
      $.get('/static/sample_transcript.txt', function(data) {
        addTranscriptData(data);
      });
    }
  };

  init();
});
