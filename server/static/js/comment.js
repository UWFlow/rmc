define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'util'],
function(RmcBackbone, $, _, util) {

  // TODO(david): Remove "Model" suffixes from other Backbone models
  var Comment = RmcBackbone.Model.extend({
    defaults: {
      comment: '',
      comment_date: new Date(0),
      anonymous: false,
      author: null,
      author_pic_url: ''
    },

    initialize: function(attributes, options) {
      if (attributes && attributes.comment_date) {
        this.set('comment_date', util.toDate(attributes.comment_date));
      }

      if (attributes && attributes.author && attributes.author.fb_pic_url) {
        this.set('author_pic_url', attributes.author.fb_pic_url);
      } else if (attributes && attributes.author &&
          attributes.author.program_name) {
        this.setProgramAvatar();
      } else {
        this.set('anonymous', true);  // TODO(david): Move this elsewhere
        this.setAnonAvatar();
      }
    },

    setAnonAvatar: function() {
      var size = [
          util.getHashCode('' + this.get('comment_date')) % 20 + 50,
          util.getHashCode(this.get('comment')) % 10 + 40
      ];
      this.set('author_pic_url',
          'http://placedog.com/g/' + size[0] + '/' + size[1]);
    },

    setProgramAvatar: function() {
      var size = [
          util.getHashCode('' + this.get('program_name')) % 20 + 50,
          util.getHashCode(this.get('program_name') + 'Z') % 10 + 40
      ];
      this.set('author_pic_url',
          'http://placekitten.com/' + size[0] + '/' + size[1]);
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
