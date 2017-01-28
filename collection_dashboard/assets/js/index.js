var tooltip = d3
  .select("body")
  .append("div")
  .attr("class", "tooltip")
  .style("opacity", 0);

function prepare_graph(id, yfunc, ylabel, yfunc2, ylabel2) {
    setTimeout(function() {
    d3.selectAll(id).selectAll(".svg-container").remove();
  var svg = d3.selectAll(id)
      .append("div")
      .classed("svg-container",true)
      .append("svg")
      .attr("preserveAspectRatio", "xMinYMin meet")
      .attr("viewBox", "0 0 500 250")
      //class to make it responsive
      .classed("svg-content-responsive", true); 
    margin = { top: 20, right: 20, bottom: 30, left: 50 },
    width = 500 - margin.left - margin.right,
    height = 250 - margin.top - margin.bottom,
    g = svg
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var x = d3.scaleTime().rangeRound([ 0, width ]);

  var y = d3.scaleLinear().rangeRound([ height, 0 ]);

  var line = d3
    .line()
    .defined(function(d) {
        try {
            result = parseFloat(yfunc(d));
            if (isNaN(result)) {
                return false;
            }
            return true;
        } catch (e) {
            return false;
        }
    })
    .x(function(d) {
      return x(d[1]);
    })
    .y(function(d) {
      return y(yfunc(d));
    });
  x.domain(
    d3.extent(micrograph_time, function(d) {
      return d[1];
    })
  );
  y.domain([
    d3.min(micrograph_time, function(d) {
        try {
      return parseFloat(yfunc(d));
        } catch (e) { return null;}
    }) * 0.9,
    d3.max(micrograph_time, function(d) {
        try {
      return parseFloat(yfunc(d));
        } catch (e) { return null; }
    }) * 1.1
  ]);
  if (arguments.length == 5) {

    var y_2 = d3.scaleLinear().rangeRound([ height, 0 ]);

  var line_2 = d3
    .line()
    .defined(function(d) {
        try {
            result = parseFloat(yfunc2(d));
            if (isNaN(result)) {
                return false;
            }
            return true;
        } catch (e) {
            return false;
        }
    })
    .x(function(d) {
      return x(d[1]);
    })
    .y(function(d) {
      return y_2(yfunc2(d));
    });
  y_2.domain([
    d3.min(micrograph_time, function(d) {
        try {
      return yfunc2(d);
        } catch (e) { return null;}
    }) * 0.9,
    d3.max(micrograph_time, function(d) {
        try {
      return yfunc2(d);
        } catch (e) { return null; }
    }) * 1.1
  ]);

  }
  g
    .append("g")
    .attr("class", "axis axis--x")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x).ticks(5));

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
    .text(ylabel);

  g.append("path").datum(micrograph_time).attr("class", "line").attr("d", line);

  g
    .selectAll(".dot")
    .data(micrograph_time)
    .enter()
    .filter(function(d) { try {
            result = parseFloat(yfunc(d));
            if (isNaN(result)) {
                return false;
            }
            return true;
    } catch (e) { return false; }
    })
    .append("circle")
    .attr("class", "dot")
    .attr("id", function(d) {
      return d[0].replace(/\//g, "_");
    })
    .attr("r", 3.5)
    .attr("cx", function(d) {
      return x(d[1]);
    })
    .attr("cy", function(d) {
      return y(yfunc(d));
    })
    .on("mouseover", function(d) {
      d3.selectAll("#" + d[0].replace(/\//g, "_") + ".dot").attr("r", 7);
      tooltip.style("opacity", 0.9);
      tooltip
        .html(d[0] + " " + d3.format(",.2f")(yfunc(d)) + "")
        .style("left", d3.event.pageX + 5 + "px")
        .style("top", d3.event.pageY - 28 + "px");
    })
    .on("mouseout", function(d) {
      d3.selectAll("#" + d[0].replace(/\//g, "_") + ".dot").attr("r", 3.5);
      tooltip.style("opacity", 0);
    })
    .on("click", function(d) {
      var url = "micrograph.html?micrograph=";
      url += d[0];
      window.location = url;
    });
    if (arguments.length == 5) {

  g
    .append("g")
    .attr("class", "axis axis--y2")
    .call(d3.axisRight(y_2))
    .append("text")
    .attr("fill", "#000")
    .attr("transform", "rotate(-90)")
    .attr("y", 6)
    .attr("dy", "0.71em")
    .style("text-anchor", "end")
    .text(ylabel2);

  g.append("path").datum(micrograph_time).attr("class", "line2").attr("d", line_2);

  g
    .selectAll(".dot")
    .data(micrograph_time)
    .enter()
    .filter(function(d) { try {
            result = parseFloat(yfunc2(d));
            if (isNaN(result)) {
                return false;
            }
            return true;
    } catch (e) { return false; }
    })
    .append("circle")
    .attr("class", "dot")
    .attr("id", function(d) {
      return d[0].replace(/\//g, "_");
    })
    .attr("r", 3.5)
    .attr("cx", function(d) {
      return x(d[1]);
    })
    .attr("cy", function(d) {
      return y_2(yfunc2(d));
    })
    .on("mouseover", function(d) {
      d3.selectAll("#" + d[0].replace(/\//g, "_") + ".dot").attr("r", 7);
      tooltip.style("opacity", 0.9);
      tooltip
        .html(d[0] + " " + d3.format(",.2f")(yfunc(d)) + "")
        .style("left", d3.event.pageX + 5 + "px")
        .style("top", d3.event.pageY - 28 + "px");
    })
    .on("mouseout", function(d) {
      d3.selectAll("#" + d[0].replace(/\//g, "_") + ".dot").attr("r", 3.5);
      tooltip.style("opacity", 0);
    })
    .on("click", function(d) {
      var url = "micrograph.html?micrograph=";
      url += d[0];
      window.location = url;
    });

    }
    }, 0);
}

function prepare_graphs(data, micrograph_time) {
  prepare_graph(
    "#grid-1-1",
    function(d) {
      return data[d[0]].moviestack.dose_per_pix_frame;
    },
    "e / (pix * frame)"
  );
  prepare_graph(
    "#grid-1-2",
    function(d) {
      return Math.sqrt(
        Math.pow(data[d[0]].MotionCor2.x_shifts[1], 2) +
          Math.pow(data[d[0]].MotionCor2.y_shifts[1], 2)
      );
    },
    "Pixels"
  );
  prepare_graph(
    "#grid-1-3",
    function(d) {
      return data[d[0]].MotionCor2.x_shifts.reduce(function(a, b, i) {
        if (i == 0)
          return 0;
        return a +
          Math.sqrt(
            Math.pow(
              data[d[0]].MotionCor2.x_shifts[i] - data[d[0]].MotionCor2.x_shifts[i - 1],
              2
            ) +
              Math.pow(
                data[d[0]].MotionCor2.y_shifts[i] - data[d[0]].MotionCor2.y_shifts[i - 1],
                2
              )
          );
      });
    },
    "Pixels"
  );
  prepare_graph(
    "#grid-3-1",
    function(d) {
      return data[d[0]].Gctf["Estimated resolution"];
    },
    "A"
  );
  prepare_graph(
    "#grid-2-1",
    function(d) {
      return (parseFloat(data[d[0]].Gctf["Defocus U"]) +
        parseFloat(data[d[0]].Gctf["Defocus V"])) /
        2;
    },
    "A"
  );
  prepare_graph(
    "#grid-2-2",
    function(d) {
      return Math.abs(data[d[0]].Gctf["Defocus U"] - data[d[0]].Gctf["Defocus V"]);
    },
    "A"
  );
  prepare_graph(
    "#grid-2-3",
    function(d) {
      return parseFloat(data[d[0]].Gctf["Astig angle"])
    },
    "Deg"
  );
  prepare_graph(
    "#grid-3-2",
    function(d) {
      return data[d[0]].Gctf["Validation scores"].reduce(
        function(a, b) {
          return a + parseInt(b);
        },
        0
      );
    },
    ""
  );
  prepare_graph(
    "#grid-3-3",
    function(d) {
      return parseFloat(data[d[0]].Gctf["Phase shift"]);
    },
    "deg"
  );
}


var glob_data;
var noCache = new Date().getTime();
var micrograph_time;

d3.timer( function () {
    try {
$('#timer').text("Last: "+countdown( micrograph_time.slice(-1)[0][1] ).toString()+ " ago");
    } catch (e) { $('#timer').text("Last:  ago"); }
},1000);
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
  prepare_graphs(data,micrograph_time);
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
  prepare_graphs(data,micrograph_time);
});
}, 20000);
