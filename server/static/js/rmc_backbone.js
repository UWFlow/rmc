define(
['ext/backbone', 'ext/jquery', 'ext/underscore'],
function(Backbone, $, _) {

  var Router = Backbone.Router.extend({});

  /**
  * A base backbone model that has been extended to our needs.
  */
  var Model = Backbone.Model.extend({
    // TODO(mack): fix _oidFields so that it is scoped per model
    _oidFields: {},
    _dateFields: {},

    _cachedReferences: {},

    /**
     * Override toJSON to convert appropriate fields to their strict
     * BSON representation before sending to the server
     *
     * For example, convert fields representing ObjectId to: { $oid: string }
     *
     * See: http://www.mongodb.org/display/DOCS/Mongo+Extended+JSON
     */
    toJSON: function(serializeBson) {
      // TODO(mack): consider resolving referenceFields in here

      var obj = this._super('toJSON');
      if (!serializeBson) {
        return obj;
      }

      function serializeOid(value) {
        if (_.isArray(value)) {
          return _.map(value, function(v) {
            return { $oid: v };
          });
        } else if (value) {
          return { $oid: value };
        }
      }

      function serializeDate(value) {
        if (_.isArray(value)) {
          return _.map(value, function(v) {
            return { $date: v.getTime() };
          });
        } else if (value) {
          return { $date: value.getTime() };
        }
      }

      _.each(this._oidFields, function(__, key) {
        obj[key] = serializeOid(obj[key]);
      });

      _.each(this._dateFields, function(__, key) {
        obj[key] = serializeDate(obj[key]);
      });

      return obj;
    },

    getReferenceFields: function() {
      if (_.isFunction(this.referenceFields)) {
        return this.referenceFields();
      } else {
        return this.referenceFields || {};
      }
    },

    getCachedReferenceKey: function(attr) {
      // Since there is only one _cachedReferences per Model type,
      // we gotta key the cache on the model's cid...until we think
      // of a better way to do this.
      return this.cid + ':' + attr;
    },

    /**
     * TODO(mack): add field to each referenceField item to
     * specify if the reference is optional.
     * TODO(mack): support passing {$oid: "XXX...."} attr
     *
     * Override get to resolve id references to other models.
     * Models should define a referenceFields attribute that
     * that is a map (or a function that returns a map) with
     * the desired reference as the key * and the id field and
     * the collection that it's cached in as the value. For example:
     * referenceFields: function() {
     *   return {
     *    'user': ['user_id', _user.Users]
     *   };
     * }
     */
    get: function(attr) {
      if (attr in this.attributes) {
        return this._super('get', arguments);
      }

      var key = this.getCachedReferenceKey(attr);
      var val;
      if (key in this._cachedReferences) {
        val = this._cachedReferences[key];
      } else {
        var referenceFields = this.getReferenceFields();

        if (!(attr in referenceFields)) {
          return;
        }

        var arr = referenceFields[attr];
        var id = this.get(arr[0]);
        if (id) {
          val = arr[1].getFromCache(id);
          this._cachedReferences[key] = val;
        }
      }
      return val;
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
      if (!attrs) {
        return this;
      }
      if (attrs instanceof Model) {
        attrs = attrs.attributes;
      }
      //if (this.idAttribute in attrs && this.constructor._cacheName) {
      //  collectionCaches[this.constructor._cacheName].add(this);
      //}

      for (attr in attrs) {
        if (attrs.hasOwnProperty(attr)) {
          val = attrs[attr];

          if (val) {
            if (_.isArray(val) && val.length && val[0].$oid) {
              // TODO(mack): This won't work if the field is supposed to
              // objectid field but starts out empty as an empty list. We might
              // need a more explicit way to state the type of each field.

              // Just gonna assume for now that if first item in array is an
              // ObjectId, entire array contains ObjectIds
              attrs[attr] = _.map(val, function(v) {
                return v.$oid;
              });
              this._oidFields[attr] = true;
            } else if (val.$oid) {
              attrs[attr] = val.$oid;
              this._oidFields[attr] = true;
            }

            if (_.isArray(val) && val.length && val[0].$date) {
              attrs[attr] = _.map(val, function(v) {
                return new Date(v.$oid);
              });
              this._dateFields[attr] = true;
            } else if (val.$date) {
              attrs[attr] = new Date(val.$date);
              this._dateFields[attr] = true;
            }
          }

          // During set, check if we are setting over an _id that is associated
          // with a reference field. If so, invalidate the key for the
          // associated reference field.
          // TODO(mack): optimize this
          var referenceFields = this.getReferenceFields();
          var cacheKey;
          _.each(referenceFields, function(arr, key) {
            if (attr === arr[0]) {
              cacheKey = this.getCachedReferenceKey(key);
              return false;
            }
          }, this);
          if (cacheKey && cacheKey in this._cachedReferences) {
            delete this._cachedReferences[cacheKey];
          }
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

    if (name in collectionCaches) {
      console.warn('Cannot create cache because a cache with name ' +
          name + ' already exists');
      return;
    }

    this._cacheName = name;
    collectionCaches[name] = {};
  };

  var normalizeId = function(id) {
    return id.$oid || id;
  };

  Collection.addToCache = function(objs) {
    // TODO(mack): enforce obj.id is set?

    if (!_.isArray(objs)) {
      objs = [objs];
    }

    var collection = collectionCaches[this._cacheName];
    _.each(objs, function(obj) {
      collection[normalizeId(obj.id)] = obj;
    });
  };

  Collection.removeFromCache = function(objs) {
    // TODO(mack): enforce obj.id is set?

    if (!_.isArray(objs)) {
      objs = [objs];
    }

    var collection = collectionCaches[this._cacheName];
    _.each(objs, function(obj) {
      delete collection[normalizeId(obj.id)];
    });
  };

  Collection._getOneFromCache = function(id) {
    var coll = collectionCaches[this._cacheName];
    if (!coll) {
      console.warn('Trying to fetch from non-existent cache ' + name);
      return undefined;
    }

    var model = coll[normalizeId(id)];
    if (!model) {
      console.warn('Did not find ' + id + ' in ' + this._cacheName);
      return undefined;
    }
    // model is already a Backbone Model
    if (model.cid) {
      return model;
    }
    coll[normalizeId(id)] = new this.prototype.model(model);
    return coll[normalizeId(id)];
  };

  Collection.getFromCache = function(ids) {
    if (!this._cacheName) {
      console.warn('A cache does not exist for this collection type');
      return undefined;
    }

    if (!ids) {
      console.warn('No ids were passed');
      return undefined;
    }

    if (_.isArray(ids)) {
      return new Collection(_.map(ids, function(id) {
        return this._getOneFromCache(id);
      }, this));
    } else {
      return this._getOneFromCache(ids);
    }
  };


  var View = Backbone.View.extend({
    close: function() {
      this.remove();
      this.unbind();
    }
  });

  var ModalView = View.extend({
    events: {
      'click .close': 'close'
    },

    show: function() {
      // Close any existing modals first
      $('body > .modal-wrapper').each(function(idx, el) {
        var modalView = $(el).data('view');
        modalView.close();
      });

      // Show this modal
      this.render();
      this.$el
        .addClass('modal-wrapper')
        .data('view', this);
      // TODO(mack): maybe should have #modal-container rather than just
      // appending to body
      $('body').append(this.$el);
    }
  });

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
      this.itemAttributes = options.itemAttributes;
    },

    /**
     * Along with the model, an additional map of attributes may be passed
     * to the individual items
     */
    createItemView: function(model, itemAttributes) {
      throw "Not implemented";
    },

    postRender: function() {
    },

    render: function() {
      this.$el.empty();
      this.collection.each(function(model) {
        var view = this.createItemView(model, this.itemAttributes);
        view.tagName = 'section';
        // TODO(david): Append all at once for faster DOM rendering
        this.$el.append(view.render().el);
      }, this);

      this.postRender();

      return this;
    }
  });

  /* jshint -W101 */
  // Add _super() helper to each function
  // From: http://pivotallabs.com/users/mbrunsfeld/blog/articles/1999-a-convenient-super-method-for-backbone-js
  /* jshint +W101 */
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
    ModalView: ModalView,
    CollectionView: CollectionView
  };
});
