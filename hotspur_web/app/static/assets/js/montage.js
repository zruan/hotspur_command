
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
		//return navigator_item.MapID == item.DrawnID;
		return true;
	});

	points.forEach( function (point) {
		if (point.PtsX.split(' ').length > 1) { return ;}
		stage_coord = [point.PtsX, point.PtsY];
		image_coord = calc_image_coordinates(stage_coord, scale_coeff, stage_center, image_center);
		ctx.beginPath();
ctx.arc(image_coord[0],image_coord[1],10,0,2*Math.PI);
		ctx.lineWidth = 10;

      // set line color
      res = Object.keys(HOTSPUR_ANNOTATION.annotation).find(function (annot) {
	      if (annot.split('/')[0].replace(/_/g, "") == navigator.replace(/_/g, "")) {
		      
		return annot.split('/')[1].split('_')[1] == point.Title.split(' ')[2];
	      }
	      return false;
      });
      console.log(res);
      color_code = { "good" : "#5cb85c", "refit" : "#f0ad4e", "bad" : '#d9534f' }
      color = undefined;
      if ( res && HOTSPUR_ANNOTATION.annotation[res].tag ) {
	      ctx.strokeStyle = color_code[HOTSPUR_ANNOTATION.annotation[res].tag];
      } else {
      ctx.strokeStyle = '#222222';
      }
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

HOTSPUR_BASE.setup_counter()
HOTSPUR_BASE.setup_navigation(previous, next)
HOTSPUR_BASE.load_data(function () {
        montage = HOTSPUR_BASE.findGetParameter("montage");
        glob_data = HOTSPUR_BASE.glob_data;
        montage_time = HOTSPUR_BASE.montage_time;
        
        if (montage == null) {
		load_montage(HOTSPUR_BASE.montage_time.slice(-1)[0][0]);
        } else {
                load_montage(montage);
        }
        
});


HOTSPUR_ANNOTATION.load_annotation(function () {
      console.log(HOTSPUR_ANNOTATION.annotation);
});
