define(["moment-timezone"], function (moment) {
    moment.tz.add({
        "zones": {
            "America/Toronto": [
                "-5 Canada E%sT"
            ]
        },
        "rules": {
            "Canada": [
                "2007 9999 2 8 0 2 0 1 D",
                "2007 9999 10 1 0 2 0 0 S"
            ]
        },
        "links": {}
    });
});
