var tooltip = d3
  .select("body")
  .append("div")
  .attr("class", "tooltip")
  .style("opacity", 0);

function prepare_graph(id, yfunc, ylabel) {
  var svg = d3.selectAll(id).append("svg").attr("height", "180").attr("width", "400"),
    margin = { top: 20, right: 20, bottom: 30, left: 50 },
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom,
    g = svg
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var x = d3.scaleTime().rangeRound([ 0, width ]);

  var y = d3.scaleLinear().rangeRound([ height, 0 ]);

  var line = d3
    .line()
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
      return yfunc(d);
    }) * 0.9,
    d3.max(micrograph_time, function(d) {
      return yfunc(d);
    }) * 1.1
  ]);

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
    .append("circle")
    .attr("class", "dot")
    .attr("id", function(d) {
      return d[0];
    })
    .attr("r", 3.5)
    .attr("cx", function(d) {
      return x(d[1]);
    })
    .attr("cy", function(d) {
      return y(yfunc(d));
    })
    .on("mouseover", function(d) {
      d3.selectAll("#" + d[0] + ".dot").attr("r", 7);
      tooltip.transition().duration(200).style("opacity", 0.9);
      tooltip
        .html(d[0] + " " + yfunc(d) + "")
        .style("left", d3.event.pageX + 5 + "px")
        .style("top", d3.event.pageY - 28 + "px");
    })
    .on("mouseout", function(d) {
      d3.selectAll("#" + d[0] + ".dot").attr("r", 3.5);
      tooltip.transition().duration(500).style("opacity", 0);
    })
    .on("click", function(d) {
      var url = "micrograph.html?micrograph=";
      url += d[0];
      window.location = url;
    });
}

var glob_data;
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
    "#grid-2-3",
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
    "#grid-3-1",
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
    "#grid-3-2",
    function(d) {
      return parseFloat(data[d[0]].Gctf["Phase shift"]);
    },
    "deg"
  );
});

