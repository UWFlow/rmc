define(
['ext/backbone', 'ext/jquery', 'ext/underscore', 'util'],
function(Backbone, $, _, util) {

  // TODO(david): Remove "Model" suffixes from other Backbone models
  var Comment = Backbone.Model.extend({
    defaults: {
      user_id: null,
      fbid: null,
      author_name: 'a puppy',
      comment: '',
      comment_date: new Date(0),
      author_pic_url: '',
      anonymous: false
    },

    initialize: function(attributes) {
      if (attributes) {
        this.set('comment_date', util.toDate(attributes.comment_date));
      }

      if (!attributes || !attributes.author_pic_url) {
        var attrs = attributes ? attributes : this.defaults;
        var size = [
            util.getHashCode('' + this.get('comment_date')) % 20 + 50,
            util.getHashCode(attrs.comment) % 10 + 40
        ];
        this.set('author_pic_url',
            'http://placedog.com/' + size[0] + '/' + size[1]);
        this.set('anonymous', true);  // TODO(david): Move this elsewhere
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
