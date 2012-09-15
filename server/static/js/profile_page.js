require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'transcript',
'term', 'course', 'friend', 'util'],
function($, _, _s, transcript, term, course, friend, util) {
  $(function() {

    // Render friend sidebar

    // TODO(mack): remove stub data
    courseIds = ['CS137', 'SCI238', 'CS241', 'MATH117', 'CS241', 'MATH137', 'CS370'];
    $.getJSON(
      '/api/courses/' + courseIds.join(','),
      function(data) {
        var courseModelById = {};
        _.each(data.courses, function(courseObj) {
          courseModelById[courseObj.id] = new course.CourseModel(courseObj);
        });
        var friendCollection = new friend.FriendCollection();
        // TODO(mack): remove stub data
        var friendsData = [
          {
            id: 541400376,
            name: 'David Hu',
            lastTermName: 'Spring 2012',
            coursesTook: [
              courseModelById['CS137'],
              courseModelById['SCI238'],
              courseModelById['CS241'],
              courseModelById['MATH117']
            ]
          },
          {
            id: 164710326,
            name: 'Mack Duan',
            lastTermName: 'Fall 2012',
            coursesTook: [
              courseModelById['CS241'],
              courseModelById['MATH137']
            ]
          },
          {
            id: 518430508,
            lastTermName: 'Fall 2012',
            name: 'Sandy Wu',
            coursesTook: [
              courseModelById['CS370']
            ]
          },
        ]
        for (var i = 0; i < 3; ++i) {
          var friendModel = new friend.FriendModel(friendsData[i]);
          friendCollection.add(friendModel);
        }
        var friendSidebarView = new friend.FriendSidebarView({
          friendCollection: friendCollection
        });
        $('#friend-sidebar-container').html(friendSidebarView.render().el);


      }
    );

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
        console.log('ex', ex.toString());
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
});
