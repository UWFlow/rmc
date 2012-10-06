define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'ratings', 'util'],
function(RmcBackbone, $, _, ratings, util) {

  // TODO(david): Remove "Model" suffixes from other Backbone models
  var Review = RmcBackbone.Model.extend({
    defaults: {
      comment: '',
      comment_date: new Date(0),
      anonymous: false,  // TODO(david): Get rid of this, replace with privacy
      author: null,
      author_pic_url: '',
      ratings: new ratings.RatingCollection()
    },

    initialize: function(attrs) {
      if (attrs && attrs.comment_date) {
        this.set('comment_date', util.toDate(attrs.comment_date));
      }

      if (attrs && attrs.author && attrs.author.fb_pic_url) {
        this.set('author_pic_url', attrs.author.fb_pic_url);
      } else if (attrs && attrs.author && attrs.author.program_name) {
        this.setProgramAvatar();
      } else {
        this.set('anonymous', true);
        this.setAnonAvatar();
      }

      if (attrs.ratings) {
        this.set('ratings', new ratings.RatingCollection(attrs.ratings));
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

  var ReviewView = RmcBackbone.View.extend({
    template: _.template($('#review-tpl').html()),
    className: 'review-post',

    initialize: function(options) {
      this.commentView = new CommentView({ model: this.model });
      this.ratingsView = new ratings.RatingChoiceCollectionView({
        collection: this.model.get('ratings'),
        readOnly: true
      });
    },

    render: function() {
      this.$el.html(this.template({}));
      this.$('.comment-placeholder').replaceWith(this.commentView.render().el);
      this.$('.ratings-placeholder').replaceWith(this.ratingsView.render().el);
      return this;
    }
  });

  var ReviewCollection = RmcBackbone.Collection.extend({
    model: Review,

    comparator: function(model) {
      return -model.get('comment_date');
    }
  });

  var ReviewCollectionView = RmcBackbone.CollectionView.extend({
    className: 'review-collection',

    createItemView: function(model) {
      return new ReviewView({ model: model });
    }
  });

  return {
    Review: Review,
    ReviewView: ReviewView,
    ReviewCollection: ReviewCollection,
    ReviewCollectionView: ReviewCollectionView
  };
});
