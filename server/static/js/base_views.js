define(
['ext/backbone', 'ext/jquery', 'ext/underscore'],
function(Backbone, $, _, _s, bootstrap) {

  /**
   * A base collection view that just renders a collection's contents into an
   * unordered list.
   *
   * Override this.createItemView to return a view to render an item given an
   * item.
   */
  var CollectionView = Backbone.View.extend({
    tagName: 'ul',

    initialize: function(options) {
      this.viewCallback = options.viewCallback;
    },

    createItemView: function(model) {
    },

    render: function() {
      this.$el.empty();
      this.collection.each(function(model) {
        var view = this.createItemView(model);
        view.tagName = 'li';
        // TODO(david): Append all at once for faster DOM rendering
        this.$el.append(view.render().el);
      }, this);

      return this;
    }
  });

  return {
    CollectionView: CollectionView
  };
});
