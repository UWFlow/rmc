define(
['ext/backbone', 'ext/jquery', 'ext/underscore'],
function(Backbone, $, _) {

  /**
   * A base collection view that just renders a collection's contents into an
   * unordered list.
   *
   * Must override this.createItemView to return a view to render an item given
   * an item.
   *
   * Optionally override this.postRender() to do stuff after this.render().
   */
  var CollectionView = Backbone.View.extend({
    tagName: 'article',

    initialize: function(options) {
      this.viewCallback = options.viewCallback;
    },

    createItemView: function(model) {
      throw "Not implemented";
    },

    postRender: function() {
    },

    render: function() {
      this.$el.empty();
      this.collection.each(function(model) {
        var view = this.createItemView(model);
        view.tagName = 'section';
        // TODO(david): Append all at once for faster DOM rendering
        this.$el.append(view.render().el);
      }, this);

      this.postRender();

      return this;
    }
  });

  return {
    CollectionView: CollectionView
  };
});
