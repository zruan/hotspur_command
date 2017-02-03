
var glob_data;
var curr_index;
var micrograph_time;
var montage_time;

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
function load_montage(montage) {
        curr_index = montage_time.findIndex(function(d) {
                return d[0] == montage;
        });
        if (glob_data[montage].montage) {
                d3
                        .selectAll("#big_micro")
                        .attr("src", "data/" + glob_data[montage].montage.preview_filename);
        } else {
                d3
                        .selectAll("#big_micro")
                        .attr("src", "");
        }
        d3.selectAll("#title_field").text(montage);
}
function previous() {
        if (curr_index > 0)
                load_montage(montage_time[curr_index - 1][0]);
}

function next() {
        if (curr_index < montage_time.length - 1)
                load_montage(montage_time[curr_index + 1][0]);
}
$("#button_previous").click(previous);
$("#button_next").click(next);
Mousetrap.bind('right', next);
Mousetrap.bind('left', previous);
d3.timer(function() {
        try {
                $('#timer').text("Last: " + countdown(micrograph_time.slice(-1)[0][1]).toString() + " ago");
        } catch (e) {
                $('#timer').text("Last:  ago");
        }
}, 1000);


var noCache = new Date().getTime();
d3.json("data/data.json" + "?_=" + noCache, function(data) {
        glob_data = data;
        micrograph_time = d3.keys(data)
		.filter(function (d) {
			if (data[d].moviestack)
	{ return true; } else { return false;}
}).map(function(d) {
                acquisition_time = d3.isoParse(data[d].moviestack.acquisition_time);
                return [d, acquisition_time];
        });

  montage_time = d3.keys(data)
		.filter(function (d) {
			if (data[d].montage)
	{ return true; } else { return false;}
}).map(function(d) {
    acquisition_time = d3.isoParse(data[d].montage.acquisition_time);
    return [ d, acquisition_time ];
  });
        function sortByDateAscending(a, b) {
                // Dates will be cast to numbers automagically:
                return a[1] - b[1];
        }
        montage_time = montage_time.sort(sortByDateAscending);
        montage = findGetParameter("montage");
        if (montage == null) {
                if (data[montage_time.slice(-1)[0][0]].montage) {
                        load_montage(montage_time.slice(-1)[0][0]);
                } else {
                        load_montage(montage_time.slice(-2)[0][0]);
                }
        } else {
                load_montage(montage);
        }
});

setInterval(function() {
if ($('#check_update').prop('checked')) {
        var noCache = new Date().getTime();
        d3.json("data/data.json" + "?_=" + noCache, function(data) {
                glob_data = data;
                micrograph_time = d3.keys(data)
		.filter(function (d) {
			if (data[d].moviestack)
	{ return true; } else { return false;}
}).map(function(d) {
                        acquisition_time = d3.isoParse(data[d].moviestack.acquisition_time);
                        return [d, acquisition_time];
                });

  montage_time = d3.keys(data)
		.filter(function (d) {
			if (data[d].montage)
	{ return true; } else { return false;}
}).map(function(d) {
    acquisition_time = d3.isoParse(data[d].montage.acquisition_time);
    return [ d, acquisition_time ];
  });
                function sortByDateAscending(a, b) {
                        // Dates will be cast to numbers automagically:
                        return a[1] - b[1];
                }
                montage_time = montage_time.sort(sortByDateAscending);
                montage = findGetParameter("montage");
                if (montage == null) {
                        if (data[montage_time.slice(-1)[0][0]].montage) {
                                load_montage(montage_time.slice(-1)[0][0]);
                        } else {
                                load_montage(montage_time.slice(-2)[0][0]);
                        }
                }
        });
}
}, 20000);
