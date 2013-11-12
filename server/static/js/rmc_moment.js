define(["moment", "moment-timezone", "ext/moment-timezone-data"], function (_moment, __, __) {
  // Always use America/Toronto as the timezone.
  return function() {
    return (_moment.apply(moment, Array.prototype.slice.apply(arguments))
            .tz("America/Toronto"));
  };
});
