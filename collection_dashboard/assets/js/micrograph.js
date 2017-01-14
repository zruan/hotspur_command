function findGetParameter(parameterName) {
  var result = null, tmp = [];
  location.search.substr(1).split("&").forEach(function(item) {
    tmp = item.split("=");
    if (tmp[0] === parameterName)
      result = decodeURIComponent(tmp[1]);
  });
  return result;
}

function create_radial_ctf_plot(micrograph) {
  d3.selectAll("#radial_plot").selectAll("svg").remove();
  var svg = d3
    .selectAll("#radial_plot")
    .append("svg")
    .attr("height", "240")
    .attr("width", "900"),
    margin = { top: 20, right: 40, bottom: 30, left: 50 },
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom,
    g = svg
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

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

function load_micrograph(micrograph) {
  curr_index = micrograph_time.findIndex(function(d) {
    return d[0] == micrograph;
  });
  d3
    .selectAll("#big_micro")
    .attr("src", "data/" + glob_data[micrograph].Preview.filename);

  d3
    .selectAll("#gctf_preview")
    .attr("src", "data/" + glob_data[micrograph].Gctf.ctf_preview_image_filename);

  d3.selectAll("#title_field").text(micrograph);
  create_radial_ctf_plot(micrograph);
}

var tooltip = d3
  .select("body")
  .append("div")
  .attr("class", "tooltip")
  .style("opacity", 0);
var glob_data;
var curr_index;
var micrograph_time;
$("#button_previous").click(function() {
  if (curr_index > 0)
    load_micrograph(micrograph_time[curr_index - 1][0]);
});
$("#button_next").click(function() {
  if (curr_index < micrograph_time.length - 1)
    load_micrograph(micrograph_time[curr_index + 1][0]);
});
d3.json("data/data.json", function(data) {
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
    load_micrograph(micrograph_time.slice(-1)[0][0]);
  } else {
    load_micrograph(micrograph);
  }
});

