define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'util'],
function(Backbone, $, _, util) {

  // TODO(david): Remove "Model" suffixes from other Backbone models
  var Comment = Backbone.Model.extend({
    defaults: {
      user_id: null,
      fbid: null,
      comment: '',
      comment_date: new Date(0)
    },

    initialize: function(attributes) {
      if (attributes) {
        this.set('comment_date', util.toDate(attributes.comment_date));
      }
    }
  });

  var CommentView = Backbone.View.extend({
    template: _.template($('#comment-tpl').html()),

    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  return {
    Comment: Comment,
    CommentView: CommentView
  };
});
