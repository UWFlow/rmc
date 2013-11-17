define(["moment", "moment-timezone", "ext/moment-timezone-data"], function (_moment, __, __) {
  // Always use America/Toronto as the timezone.
  return function rmc_moment(a, b, c, d) {
    countMe("rmc_moment");
    return _moment(a, b, c, d)
        .tz("America/Toronto");
  };
});
