define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'util'],
function(RmcBackbone, $, _, util) {

  // TODO(david): Remove "Model" suffixes from other Backbone models
  var Comment = RmcBackbone.Model.extend({
    defaults: {
      comment: '',
      comment_date: new Date(0),
      anonymous: false,
      author: {
        'name': 'a puppy'
      },
      author_pic_url: ''
    },

    initialize: function(attributes, options) {
      if (attributes && attributes.comment_date) {
        this.set('comment_date', util.toDate(attributes.comment_date));
      }

      if (attributes && attributes.author && attributes.author.fb_pic_url) {
        this.set('author_pic_url', attributes.author.fb_pic_url);
      } else {
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

  var CommentView = RmcBackbone.View.extend({
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
