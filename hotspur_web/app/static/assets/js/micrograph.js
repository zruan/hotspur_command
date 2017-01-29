function findGetParameter(parameterName) {
  var result = null, tmp = [];
  location.search.substr(1).split("&").forEach(function(item) {
    tmp = item.split("=");
    if (tmp[0] === parameterName)
      result = decodeURIComponent(tmp[1]);
  });
  return result;
}

function create_micrograph_info(micrograph) {
    labelfields = d3.selectAll("#micrograph_information").selectAll("h4");
    labelfields.datum(function() { return this.dataset; })
                .text(function(d) { return glob_data[micrograph][d.label.split('.')[0]][d.label.split('.')[1]]; });
}

function create_motion_chart(micrograph) {
  d3.selectAll("#motion_chart").selectAll(".svg-container").remove();
  var svg = d3.selectAll("#motion_chart")
      .append("div")
      .classed("svg-container",true)
      .classed("motion",true)
      .append("svg")
      .attr("preserveAspectRatio", "xMinYMin meet")
      .attr("viewBox", "0 0 300 300")
      //class to make it responsive
      .classed("svg-content-responsive", true), 
    margin = { top: 20, right: 20, bottom: 20, left: 20 },
    width = 300 - margin.left - margin.right,
    height = 300 - margin.top - margin.bottom,
    g = svg
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var x = d3.scaleLinear().rangeRound([ width, 0 ]);

  var y = d3.scaleLinear().rangeRound([ height, 0 ]);
  x.domain([-20,20]);
  y.domain([-20,20]);
  g
    .append("g")
    .attr("class", "axis axis--x")
    .attr("transform", "translate(0," + height/2 + ")")
    .call(d3.axisBottom(x));

  g
    .append("g")
    .attr("class", "axis axis--y")
    .call(d3.axisLeft(y))
    .attr("transform", "translate(" + width/2 + ",0)")
    .append("text")
    .attr("fill", "#000")
    .attr("transform", "rotate(-90)")
    .attr("y", 6)
    .attr("dy", "0.71em")
    .style("text-anchor", "end")
    .text("");
  if (glob_data[micrograph].MotionCor2) {
  var line = d3
    .line()
    .x(function(d, i) {
      return x(parseFloat(glob_data[micrograph].MotionCor2.x_shifts[i]));
    })
    .y(function(d, i) {
      return y(parseFloat(glob_data[micrograph].MotionCor2.y_shifts[i]));
    });
  g
    .append("path")
    .datum(glob_data[micrograph].MotionCor2.x_shifts)
    .attr("class", "line motion")
    .attr("d", line);
  }
}


function create_radial_ctf_plot(micrograph) {
    d3.selectAll("#radial_plot").selectAll(".svg-container").remove();
  var svg = d3.selectAll("#radial_plot")
      .append("div")
      .classed("svg-container",true)
      .classed("ctf",true)
      .append("svg")
      .attr("preserveAspectRatio", "xMinYMin meet")
      .attr("viewBox", "0 0 750 300")
      //class to make it responsive
      .classed("svg-content-responsive", true), 
    margin = { top: 20, right: 20, bottom: 30, left: 50 },
    width = 750 - margin.left - margin.right,
    height = 300 - margin.top - margin.bottom,
    g = svg
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  if ( glob_data[micrograph].Gctf ) {
  var x = d3.scaleLinear().rangeRound([ width, 0 ]);

  var y = d3.scaleLinear().rangeRound([ height, 0 ]);
  var back_y = d3.scaleLinear().rangeRound([ height, 0 ]);

  x.domain(d3.extent(glob_data[micrograph].Gctf.EPA.Resolution));
  y.domain(d3.extent(glob_data[micrograph].Gctf.EPA["Sim. CTF"]));
  back_y.domain(d3.extent(glob_data[micrograph].Gctf.EPA["Meas. CTF - BG"]));

  var line = d3
    .line()
    .x(function(d, i) {
      return x(parseFloat(glob_data[micrograph].Gctf.EPA.Resolution[i]));
    })
    .y(function(d, i) {
      return y(parseFloat(glob_data[micrograph].Gctf.EPA["Sim. CTF"][i]));
    });

  var back_line = d3
    .line()
    .x(function(d, i) {
      return x(parseFloat(glob_data[micrograph].Gctf.EPA.Resolution[i]));
    })
    .y(function(d, i) {
      return back_y(parseFloat(glob_data[micrograph].Gctf.EPA["Meas. CTF - BG"][i]));
    });

  g
    .append("g")
    .attr("class", "axis axis--x")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x));

  g
    .append("g")
    .attr("class", "axis axis--y")
    .call(d3.axisLeft(y))
    .append("text")
    .attr("fill", "#000")
    .attr("transform", "rotate(-90)")
    .attr("y", 6)
    .attr("dy", "0.71em")
    .style("text-anchor", "end")
    .text("");

  g
    .append("g")
    .attr("class", "axis axis--y")
    .call(d3.axisRight(back_y))
    .attr("transform", "translate(" + width + ",0)")
    .append("text")
    .attr("fill", "#000")
    .attr("transform", "rotate(-90)")
    .attr("y", 6)
    .attr("dy", "0.71em")
    .style("text-anchor", "end")
    .text("");
  g
    .append("path")
    .datum(glob_data[micrograph].Gctf.EPA.Resolution)
    .attr("class", "line simctf")
    .attr("d", line);
  g
    .append("path")
    .datum(glob_data[micrograph].Gctf.EPA.Resolution)
    .attr("class", "line")
    .attr("d", back_line);
  }
}

function load_micrograph(micrograph) {
  curr_index = micrograph_time.findIndex(function(d) {
    return d[0] == micrograph;
  });
  if (glob_data[micrograph].MotionCor2) {
  d3
    .selectAll("#big_micro")
    .attr("src", "data/" + glob_data[micrograph].MotionCor2.preview_filename);
  } else {
  d3
    .selectAll("#big_micro")
    .attr("src", "" );
  }
  if (glob_data[micrograph].Gctf) {
  d3
    .selectAll("#gctf_preview")
    .attr("src", "data/" + glob_data[micrograph].Gctf.ctf_preview_image_filename);
  } else {
  d3
    .selectAll("#gctf_preview")
    .attr("src", "" );
  }
  d3.selectAll("#title_field").text(micrograph);
  create_radial_ctf_plot(micrograph);
  create_motion_chart(micrograph);
  create_micrograph_info(micrograph);
}

var tooltip = d3
  .select("body")
  .append("div")
  .attr("class", "tooltip")
  .style("opacity", 0);
var glob_data;
var curr_index;
var micrograph_time;
function previous() {
  if (curr_index > 0)
    load_micrograph(micrograph_time[curr_index - 1][0]);
}
function next() {
  if (curr_index < micrograph_time.length - 1)
    load_micrograph(micrograph_time[curr_index + 1][0]);
}
$("#button_previous").click(previous);
$("#button_next").click(next);
Mousetrap.bind('right', next);
Mousetrap.bind('left', previous);
d3.timer( function () {
    try {
$('#timer').text("Last: "+countdown( micrograph_time.slice(-1)[0][1] ).toString()+ " ago");
    } catch (e) { $('#timer').text("Last:  ago"); }
},1000);


var noCache = new Date().getTime();
d3.json("data/data.json" + "?_=" + noCache, function(data) {
  glob_data = data;
  micrograph_time = d3.keys(data).map(function(d) {
    acquisition_time = d3.isoParse(data[d].moviestack.acquisition_time);
    return [ d, acquisition_time ];
  });
  function sortByDateAscending(a, b) {
    // Dates will be cast to numbers automagically:
    return a[1] - b[1];
  }
  micrograph_time = micrograph_time.sort(sortByDateAscending);
  micrograph = findGetParameter("micrograph");
  if (micrograph == null) {
    if (data[micrograph_time.slice(-1)[0][0]].MotionCor2) {
    load_micrograph(micrograph_time.slice(-1)[0][0]);
    } else {
    load_micrograph(micrograph_time.slice(-2)[0][0]);
    }
  } else {
    load_micrograph(micrograph);
  }
});

setInterval(function () {
var noCache = new Date().getTime();
d3.json("data/data.json" + "?_=" + noCache, function(data) {
  glob_data = data;
  micrograph_time = d3.keys(data).map(function(d) {
    acquisition_time = d3.isoParse(data[d].moviestack.acquisition_time);
    return [ d, acquisition_time ];
  });
  function sortByDateAscending(a, b) {
    // Dates will be cast to numbers automagically:
    return a[1] - b[1];
  }
  micrograph_time = micrograph_time.sort(sortByDateAscending);
  micrograph = findGetParameter("micrograph");
  if (micrograph == null) {
    if (data[micrograph_time.slice(-1)[0][0]].MotionCor2) {
    load_micrograph(micrograph_time.slice(-1)[0][0]);
    } else {
    load_micrograph(micrograph_time.slice(-2)[0][0]);
    }
  } 
});
},20000);
