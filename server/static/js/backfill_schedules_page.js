/* global mixpanel */
require(
['ext/jquery', 'ext/underscore', 'ext/underscore.string', 'ext/bootstrap',
'util', 'schedule_parser'],
function($, _, _s, __, _util, _schedule_parser) {
  var $logger = $('#logger');

  // Set up the logging box to be scrolled to bottom, unless the user
  // explicitly scrolls up.
  var append = $logger.append;
  $logger.append = function(elem) {
    var atBottom = $logger[0].scrollTop + 25 >=
      ($logger[0].scrollHeight - $logger[0].offsetHeight);

    _.bind(append, this)(elem);

    if (atBottom) {
      $logger.scrollTop(99999999);
    }
  };

  // TODO(mack): get bootstrap's .button() working

  $('#backfill-all-btn').click(function(evt) {
    if ($(this).hasClass('disabled')) {
      return false;
    }
    $('button').addClass('disabled');

    $logger.append(
      '<div class="text-info">Fetching all users who have schedules</div>');
    $.ajax('/api/users/schedule_paste', {
      type: 'GET',
      data: {
        include_good_paste: true,
        include_bad_paste: true
      },
      error: function(xhr) {
        $logger.append('<div class="text-error">Error fetching all users: ' +
            _.escape(xhr.statusText) + '</div>');
      }
    }).then(function(data) {
      data = JSON.parse(data);
      var userIds = data.user_ids;
      $logger.append('<div class="text-info">Fetched ' + userIds.length +
          ' users</div>');

      processUsers(userIds);
    });
  });

  $('#backfill-failed-btn').click(function(evt) {
    if ($(this).hasClass('disabled')) {
      return false;
    }
    $('button').addClass('disabled');

    $logger.append(
      '<div class="text-info">Fetching users whose schedule failed ' +
      'to parse</div>');
    $.ajax('/api/users/schedule_paste', {
      type: 'GET',
      data: {
        include_bad_paste: true
      },
      error: function(xhr) {
        $logger.append('<div class="text-error">Error fetching failed users: ' +
            _.escape(xhr.statusText) + '</div>');
      }
    }).then(function(data) {
      data = JSON.parse(data);
      var userIds = data.user_ids;
      $logger.append('<div class="text-info">Fetched ' + userIds.length +
          ' users</div>');

      processUsers(userIds);
    });
  });

  $('#backfill-screenshots-btn').on('click', function(evt) {
    var $this = $(this);
    $this.prop('disabled', true);

    $.post('/api/schedules/backfill_screenshots', function() {
      $logger.append(
        '<div class="text-info">Schedule screenshots backfill started.<br>' +
        'Only schedules that are out of date will be re-rendered.</div>');
      $this.prop('disabled', false);
    });
  });

  $('#backfill-userid-btn').click(function(evt) {
    var userId = $('#backfill-userid-input').val();

    if ($(this).hasClass('disabled') || userId === '') {
      return false;
    }
    $('button').addClass('disabled');

    $logger.append('<div class="text-info">Backfill user ' + userId + '</div>');

    var users = [{ $oid: userId }];
    processUsers(users);
  });

  function processUsers(userIds) {
    var idx = 0;
    var failedCount = 0;
    processUser();

    function processUser() {
      if (idx >= userIds.length) {
        $('button').removeClass('disabled');
        $logger.append('<div class="text-info">Finished processing all users ' +
          'with ' + failedCount + ' failures</div>');
        return;
      }

      var userId = userIds[idx];

      $logger.append('<div class="muted">User ' + (idx + 1) + ': ' +
          userId.$oid +'</div>');

      $.ajax('/api/user/last_schedule_paste', {
        type: 'GET',
        data: {
          user_id: userId.$oid
        },
        error: function(xhr) {
          $logger.append('<div class="text-error indent">Error getting last ' +
              'pasted schedule: ' + _.escape(xhr.statusText) + '</div>');
          failedCount += 1;
        }
      }).then(
        function (data) {
          data = JSON.parse(data);

          $logger.append('<div class="muted indent">Fetched schedule</div>');

          var scheduleText = data.last_schedule_paste;
          var scheduleData;
          try {
            scheduleData = new _schedule_parser.parseSchedule(scheduleText);
          } catch(ex) {
            $logger.append(
              '<div class="text-error indent">Error while parsing: ' +
              ex.toString() +'</div>');
            failedCount += 1;
            return $.Deferred().reject();
          }

          return $.ajax('/api/schedule', {
            type: 'POST',
            data: {
              'schedule_text': scheduleText,
              'schedule_data': JSON.stringify(scheduleData),
              'as_oid': userId.$oid
            },
            error: function(xhr) {
              $logger.append('<div class="text-error indent">Error saving ' +
                  'schedule: ' + _.escape(xhr.statusText) + '</div>');
              failedCount += 1;
            }
          });
        }
      ).then(
        function(data) {
          $logger.append('<div class="muted indent">Successfully ' +
              'saved schedule</div>');
        }
      ).always(function() {
        if (idx < userIds.length) {
          idx += 1;
          window.setTimeout(processUser, 0);
        }
      });
    }
  }

  mixpanel.track('Impression: Backfill Schedules Page');

  $(document.body).trigger('pageScriptComplete');
});
