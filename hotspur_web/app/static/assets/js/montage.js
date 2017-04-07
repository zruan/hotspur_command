
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
	setup_canvas(montage);
}
function setup_canvas(montage) {
	var canvas = $('#big_micro_canvas')[0];
	var ctx = canvas.getContext("2d");
	var navigator = undefined;
	if (montage.split("_")[0] in glob_data && glob_data[montage.split("_")[0]].navigator) {
		navigator = montage.split("_")[0];
	}
	if (montage.split("_").slice(0,2).join('') in glob_data && glob_data[montage.split("_").slice(0,2).join('')].navigator) {
		navigator = montage.split("_").slice(0,2).join('');
	}
	if (navigator == undefined) { return; }
	var navigator_item = glob_data[navigator].navigator.items.find(function (item) {
		return item.Note && item.Note.split(' ')[3] == montage + '.mrc';
	});

	if (navigator_item == undefined) { 
	navigator_item = glob_data[navigator].navigator.items.find(function (item) {
		if(item.Note && item.Note.split(' ')[3] == montage.substring(0,montage.length-3) + '.mrc') {
			if (parseInt(item.Note.split(' ')[1]) == parseInt(montage.substring(montage.length-3,montage.length) )) { return true; }
			else {return false;}
		}
	});
	if (navigator_item == undefined) { return ;}
}
	canvas.width = navigator_item.MapWidthHeight.split(' ')[0];
	canvas.height = navigator_item.MapWidthHeight.split(' ')[1];
	image_center = [canvas.width/2, canvas.height/2];
	stage_center = navigator_item.RawStageXY.split(' ');
	scale_coeff = navigator_item.MapScaleMat.split(' ');

	points = glob_data[navigator].navigator.items.filter( function (item) {
		return navigator_item.MapID == item.DrawnID;
	});

	points.forEach( function (point) {
		if (point.PtsX.split(' ').length > 1) { return ;}
		stage_coord = [point.PtsX, point.PtsY];
		image_coord = calc_image_coordinates(stage_coord, scale_coeff, stage_center, image_center);
		console.log(image_coord)
		ctx.beginPath();
ctx.arc(image_coord[0],image_coord[1],10,0,2*Math.PI);
		ctx.lineWidth = 10;

      // set line color
      ctx.strokeStyle = '#ff0000';
ctx.stroke();
	});

}

function calc_image_coordinates(stage_coord, scale_coeff, stage_center, image_center) {
	var X = scale_coeff[0] * (stage_coord[0] - stage_center[0]) +scale_coeff[1] * (stage_coord[1] - stage_center[1]) + image_center[0];
	var Y = scale_coeff[2] * (stage_coord[0] - stage_center[0]) +scale_coeff[3] * (stage_coord[1] - stage_center[1]) + image_center[1];
	return [X,Y];
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
