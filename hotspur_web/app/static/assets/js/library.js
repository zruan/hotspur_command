var HOTSPUR_BASE = (function ($,d3) {
    var my = {}
    var glob_data;
    var micrograph_time;
    var montage_time;

    // Private 



    // Public functions
                
    function findGetParameter(parameterName) {
        var result = null,
                tmp = [];
        location.search.substr(1).split("&").forEach(function(item) {
                tmp = item.split("=");
                if (tmp[0] === parameterName)
                        result = decodeURIComponent(tmp[1]);
        });
        return result;
    }

    function setup_ui() {
             d3.timer(function () {
            try {
                $('#timer').text("Last: " + countdown(micrograph_time.slice(-1)[0][1]).toString() + " ago");
            } catch (e) {
                $('#timer').text("Last:  ago");
            }
        }, 1000);
    }

    function load_data(callback) {

        var noCache = new Date().getTime();


       
        d3.json("data/data.json" + "?_=" + noCache, function (data) {
            glob_data = data;
            micrograph_time = d3.keys(data)
                .filter(function (d) {
                    if (data[d].moviestack) {
                        return true;
                    } else {
                        return false;
                    }
                })
                .map(function (d) {
                    acquisition_time = d3.isoParse(data[d].moviestack.acquisition_time);
                    return [d, acquisition_time];
                });
            montage_time = d3.keys(data)
                .filter(function (d) {
                    if (data[d].montage) {
                        return true;
                    } else {
                        return false;
                    }
                }).map(function (d) {
                    acquisition_time = d3.isoParse(data[d].montage.acquisition_time);
                    return [d, acquisition_time];
                });

            function sortByDateAscending(a, b) {
                // Dates will be cast to numbers automagically:
                return a[1] - b[1];
            }
            micrograph_time = micrograph_time.sort(sortByDateAscending);
            callback(my);
        });

    }

    my.setup_ui = setup_ui;
    my.load_data = load_data;

    my.glob_data = glob_data;
    my.micrograph_time = micrograph_time;
    my.montage_time = montage_time;
       
    

}());