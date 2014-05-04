define(function() {
  var programToString = function(program) {
    if (program) {
      return program;
    } else {
      return "";
    }
  };

  var formatCourseResult = function(course) {
    return '<a style="display:block;"><i class="icon-book search-icon"></i>'+
        '<b>'+course.label.toUpperCase()+'</b> &nbsp;&nbsp;&nbsp;&nbsp;'+
        course.name + '</a>';
  };

  var formatFriendResult = function(friend) {
    return '<a style="display:block;"><img src="'+friend.pic +
        '" width="20" height="20">'+'<b>'+friend.label+'</b> &nbsp;&nbsp;' +
        programToString(friend.program)+'</a>';
  };

  return {
    formatCourseResult: formatCourseResult,
    formatFriendResult: formatFriendResult
  };
});
