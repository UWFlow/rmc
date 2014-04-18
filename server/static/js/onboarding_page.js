require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'transcript',
'util', 'rmc_backbone', 'user', 'ext/bootstrap'],
function($, _, _s, transcript, _util, RmcBackbone, _user, __) {

  var AddTranscriptView = RmcBackbone.View.extend({
    className: 'add-transcript',

    initialize: function(attributes) {
      this.friends = attributes.friends;
      this.user = attributes.user;
      var friends = this.user.get('friends');
      this.transcriptFriends = new _user.UserCollection();
      friends.each(function(friend) {
        if (friend.get('course_history').length) {
          this.transcriptFriends.add(friend);
        }
      }, this);
      this.template = _.template($('#add-transcript-tpl').html());
    },

    render: function() {
      this.$el.html(this.template({
        transcript_friends: this.transcriptFriends
      }));

      this.$('[rel="tooltip"]').tooltip();

      if (_util.getQueryParam('test')) {
        $.get('/static/sample_transcript.txt', _.bind(function(data) {
          this.addTranscriptData(data);
        }, this));
      }

      _.defer(_.bind(this.postRender, this));

      return this;
    },

    postRender: function() {
      this.$('.transcript-text').height(
        this.$('.friends-added-transcript').height());
    },

    events: {
      'input .transcript-text': 'inputTranscript',
      'paste .transcript-text': 'inputTranscript'
    },

    inputTranscript: function(evt) {
      this.$('.transcript-error').empty();

      // Store the transcript text
      var data = $(evt.currentTarget).val();
      if (!data) {
        // If the text area has been emptied, exit immediately w/o
        // showing error message for parse failure.
        return;
      }

      this.addTranscriptData(data);
    },

    addTranscriptData: function(data) {
      // Try/catch around parsing logic so that we show error message
      // should anything go wrong
      var transcriptData;
      var coursesByTerm;
      try {
        transcriptData = transcript.parseTranscript(data);
        coursesByTerm = transcriptData.coursesByTerm;
      } catch (ex) {
        $.ajax('/api/transcript/log', {
          data: {
            transcript: transcript.removeGrades(data)
          },
          type: 'POST'
        });

        console.warn('Could not parse transcript', ex);
        this.$('.transcript-error').text(
            'Uh oh. Could not parse your transcript :( ' +
            'Please check that you\'ve pasted your transcript correctly.');

        mixpanel.track('Transcript parse error', { error_msg: ex.toString() });
        return;
      }

      // TODO(mack): fix confusing names between term/termObj and
      // course/courseObj
      var courseIds = [];
      _.each(coursesByTerm, function(termObj) {
        _.each(termObj.courseIds, function(courseId) {
          courseIds.push(courseId);
        });
      });

      // TODO(Sandy): This assumes the /transcript request will succeed and that
      // google's servers are faster than ours, which may not be the case. But
      // if we make this request in the success handler, it might not get logged
      // at all (due to the redirect). We could setTimeout the redirect, but
      // that would cause delay and also since /transcript should just be
      // succesful, we'll do this for now. Maybe move to server side.
      _gaq.push([
        '_trackEvent',
        'USER_GENERIC',
        'TRANSCRIPT_UPLOAD'
      ]);
      mixpanel.track('Transcript uploaded');
      $.post(
        '/api/transcript',
        {
          'transcriptData': JSON.stringify(transcriptData)
        },
        function() {
          // TODO(mack): load and update page with js rather than reloading
          // Fail safe to make sure at least we sent off the _gaq trackEvent
          _gaq.push(function() {
            var redirectUrl = _util.getQueryParam('next');
            if (redirectUrl) {
              window.location.href = redirectUrl;
            } else {
              window.location.href = '/profile';
            }
          });
        },
        'json'
      );
    }

  });

  var init = function() {
    _user.UserCollection.addToCache(pageData.userObjs);
    var addTranscriptView = new AddTranscriptView({
      user: _user.UserCollection.getFromCache(pageData.currentUserId.$oid)
    });

    $('#add-transcript-container')
      .html(addTranscriptView.render().el);

    var redirectUrl = _util.getQueryParam('next');
    if (redirectUrl) {
      $('.skip-link').attr('href', redirectUrl);
    }
  };

  init();

  mixpanel.track('Impression: Onboarding page');

  $(document.body).trigger('pageScriptComplete');
});
