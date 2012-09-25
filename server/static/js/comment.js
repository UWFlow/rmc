define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'util'],
function(Backbone, $, _, util) {

  // TODO(david): Remove "Model" suffixes from other Backbone models
  var Comment = Backbone.Model.extend({
    defaults: {
      user_id: null,
      fbid: null,
      comment: '',
      comment_date: new Date(0),
      author_pic_url: ''
    },

    initialize: function(attributes) {
      if (attributes) {
        this.set('comment_date', util.toDate(attributes.comment_date));
      }

      if (!attributes || !attributes.author_pic_url) {
        var attrs = attributes ? attributes : this.defaults;
        var size = [
            util.getHashCode('' + this.get('comment_date')) % 20 + 80,
            util.getHashCode(attrs.comment) % 20 + 80
        ];
        this.set('author_pic_url',
            'http://placedog.com/' + size[0] + '/' + size[1]);
      }
    }
  });

  var CommentView = Backbone.View.extend({
    template: _.template($('#comment-tpl').html()),
    className: 'comment',

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
