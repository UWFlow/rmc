define(
['rmc_backbone', 'ext/jquery', 'ext/underscore', 'comment', 'ratings'],
function(RmcBackbone, $, _, comment, ratings) {

  // TODO(david): Remove "Model" suffixes from other Backbone models
  // TODO(david): Remove the comment being nested
  var Review = RmcBackbone.Model.extend({
    defaults: {
      comment: new comment.Comment(),
      ratings: new ratings.RatingCollection()
    },

    initialize: function(attributes) {
      if (attributes.comment) {
        this.set('comment', new comment.Comment(attributes.comment));
      }

      if (attributes.ratings) {
        this.set('ratings', new ratings.RatingCollection(attributes.ratings));
      }
    }
  });

  var ReviewView = RmcBackbone.View.extend({
    template: _.template($('#review-tpl').html()),
    className: 'review-post',

    initialize: function(options) {
      this.commentView = new comment.CommentView({
        model: this.model.get('comment')
      });
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
      return -model.get('comment').get('comment_date');
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
