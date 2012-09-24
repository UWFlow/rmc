define(
['ext/backbone', 'ext/jquery', 'ext/underscore'],
function(Backbone, $, _) {

  // TODO(david): Remove "Model" suffixes from other Backbone models
  var Comment = Backbone.Model.extend({
    defaults: {
      user_id: null,
      fbid: null,
      comment: '',
      comment_date: new Date(0)
    }
  });

  var CommentView = Backbone.View.extend({
    //template: _.template($('#comment-tpl')),
    template: _.template(''),

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
