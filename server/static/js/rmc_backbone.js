define(
['ext/backbone', 'ext/jquery', 'ext/underscore'],
function(Backbone, $, _) {

  var Router = Backbone.Router.extend({});

  /**
  * A base backbone model that has been extended to our needs.
  */
  var Model = Backbone.Model.extend({
    _oidFields: {},

    /**
     * Override toJSON to convert appropriate string fields to { $oid: string }
     * if the field represents an ObjectId
     */
    toJSON: function(resolveOids) {
      var obj = this._super('toJSON');
      if (resolveOids) {
        _.each(this._oidFields, function(__, key) {
          var value = obj[key];
          if (typeof value === 'string') {
            value = { $oid: value };
          } else if (_.isArray(value)) {
            value = _.map(value, function(v) {
              return { $oid: v };
            });
          }
        });
      }
      return obj;
    },

    /**
    * Override set to convert ObjectId fields { $oid: string } to string fields
    */
    set: function(key, value, options) {
      var attrs, attr, val;

      // Handle both `"key", value` and `{key: value}` -style arguments.
      if (_.isObject(key) || key === null) {
        attrs = key;
        options = value;
      } else {
        attrs = {};
        attrs[key] = value;
      }

      // Extract attributes and options.
      if (!attrs) return this;
      if (attrs instanceof Model) attrs = attrs.attributes;
      //if (this.idAttribute in attrs && this.constructor._cacheName) {
      //  collectionCaches[this.constructor._cacheName].add(this);
      //}

      for (attr in attrs) {
        val = attrs[attr];
        if (val && typeof val.$oid === 'string') {
          attrs[attr] = val.$oid;
          this._oidFields[attr] = true;
        } else if (_.isArray(val) && val.length &&
            typeof val[0].$oid === 'string') {
          // Just gonna assume for now that if first item in array is an
          // ObjectId, entire array contains ObjectIds
          attrs[attr] = _.map(val, function(v) {
            return v.$oid;
          });
          this._oidFields[attr] = true;
        }
      }

      return this._super('set', [attrs, options]);
    }
  });

  var Collection = Backbone.Collection.extend({});

  var collectionCaches = {};

  Collection.registerCache = function(name) {
    if (!name) {
      console.warn('Cannot create cache because name is empty');
      return;
    }
    this._cacheName = name;
    var collection = new this();
    // TODO(mack): might wanna consider auto-caching Models when they
    // are created, hover this might be too magical.
    // collection.model._cacheName = name;
    collectionCaches[name] = collection;
  };

  Collection.addToCache = function(objs) {
    // TODO(mack): enforce obj.id is set?

    if (!_.isArray(objs)) {
      objs = [objs];
    }

    var collection = collectionCaches[this._cacheName];
    // Prevent validation of models on initial add
    collection.add(objs, {silent: true});
  };

  Collection.getFromCache = function(ids) {
    if (!this._cacheName) {
      console.warn('A cache does not exist for this collection type');
      return undefined;
    }

    if (!ids) {
      console.warn('No ids were passed');
      console.trace();
      return undefined;
    }

    var coll = collectionCaches[this._cacheName];
    if (!coll) {
      console.warn('Trying to fetch from non-existent cache ' + name);
      return undefined;
    }

    if (_.isArray(ids)) {
      return new this(_.map(ids, function(id) {
        var model =  coll.get(id);
        if (!model) {
          console.warn('Did not find ' + id + ' in ' + this._cacheName);
          console.trace();
        }
        return model;
      }, this));
    } else {
      return coll.get(ids);
    }
  };


  var View = Backbone.View.extend({});

  /**
   * A base collection view that just renders a collection's contents into an
   * unordered list.
   *
   * Must override this.createItemView to return a view to render an item given
   * an item.
   *
   * Optionally override this.postRender() to do stuff after this.render().
   */
  var CollectionView = View.extend({
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

  // Add _super() helper to each function
  // From: http://pivotallabs.com/users/mbrunsfeld/blog/articles/1999-a-convenient-super-method-for-backbone-js
  (function(klasses) {

    // The super method takes two parameters: a method name
    // and an array of arguments to pass to the overridden method.
    // This is to optimize for the common case of passing 'arguments'.
    function _super(methodName, args) {

      // Keep track of how far up the prototype chain we have traversed,
      // in order to handle nested calls to _super.
      if (!this._superCallObjects) {
        this._superCallObjects = {};
      }
      var currentObject = this._superCallObjects[methodName] || this,
          parentObject  = findSuper(methodName, currentObject);
      this._superCallObjects[methodName] = parentObject;

      var result = parentObject[methodName].apply(this, args || []);
      delete this._superCallObjects[methodName];
      return result;
    }

    // Find the next object up the prototype chain that has a
    // different implementation of the method.
    function findSuper(methodName, childObject) {
      var object = childObject;
      while (object[methodName] === childObject[methodName]) {
        object = object.constructor.__super__;
      }
      return object;
    }

    _.each(klasses, function(klass) {
      klass.prototype._super = _super;
    });

  })([Model, Collection, View, Router]);

  return {
    Router: Router,
    Model: Model,
    Collection: Collection,
    View: View,
    CollectionView: CollectionView
  };
});
