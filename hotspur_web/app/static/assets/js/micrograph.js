var LABELS = [{
        "label": "Acquisition Date",
        "callback": function (d) {
                time = d3.isoParse(d.moviestack.acquisition_time);
                return d3.timeFormat("%B %d, %Y %I:%M %p")(time);
        }
},
{
        "label": "Number of frames",
        "callback": function (d) {
                return d.moviestack.numframes;
        }
},
{
        "label": "Dose rate",
        "callback": function (d) {
                return d3.format(".2f")(d.moviestack.dose_per_pix_frame) + " e/pix/frame";
        }
},
{
        "label": "Defocus",
        "callback": function (d) {
                return d3.format(".2f")((parseFloat(d.Gctf["Defocus U"])
                        + parseFloat(d.Gctf["Defocus V"])) / 20000) + " µm";
        }
},
{
        "label": "Astigmatism",
        "callback": function (d) {
                return d3.format(".2f")(Math.abs(parseFloat(d.Gctf["Defocus U"])
                        - parseFloat(d.Gctf["Defocus V"])) / 10000)
                        + " µm at " + d3.format(".1f")(parseFloat(d.Gctf["Astig angle"])) + "°";
        }
},
{
        "label": "Gctf resolution estimate",
        "callback": function (d) {
                return d3.format(".2f")(d.Gctf["Estimated resolution"]) + " ‫";
        }
},
{
        "label": "Gctf validation score",
        "callback": function (d) {
                return String(d.Gctf["Validation scores"].reduce(
                        function (a, b) {
                                return a + parseInt(b);
                        },
                        0
                )) +
                        d.Gctf["Validation scores"].reduce(
                                function (a, b) {
                                        return a + "," + b;
                                },
                                "("
                        ) + ")";
        }
},
];


function create_micrograph_info(micrograph) {
        labels = LABELS;
        d3.selectAll("#micrograph_information").selectAll("div").remove();
        container = d3.selectAll("#micrograph_information").selectAll("div");
        label_fields = container.data(labels).enter().append("div")
                .classed("col-xs-4", true);
        label_fields.append("small").text(function (d) {
                return d.label;
        });
        label_fields.append("h4").text(function (d) {
                return d.callback(glob_data[micrograph]);
        });
}

function create_motion_chart(micrograph) {
        d3.selectAll("#motion_chart").selectAll(".svg-container").remove();
        var svg = d3.selectAll("#motion_chart")
                .append("div")
                .classed("svg-container", true)
                .classed("motion", true)
                .append("svg")
                .attr("preserveAspectRatio", "xMinYMin meet")
                .attr("viewBox", "0 0 300 300")
                //class to make it responsive
                .classed("svg-content-responsive", true),
                margin = {
                        top: 20,
                        right: 20,
                        bottom: 20,
                        left: 20
                },
                width = 300 - margin.left - margin.right,
                height = 300 - margin.top - margin.bottom,
                g = svg
                        .append("g")
                        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var x = d3.scaleLinear().rangeRound([width, 0]);

        var y = d3.scaleLinear().rangeRound([height, 0]);
        x.domain([-20, 20]);
        y.domain([-20, 20]);
        g
                .append("g")
                .attr("class", "axis axis--x")
                .attr("transform", "translate(0," + height / 2 + ")")
                .call(d3.axisBottom(x));

        g
                .append("g")
                .attr("class", "axis axis--y")
                .call(d3.axisLeft(y))
                .attr("transform", "translate(" + width / 2 + ",0)")
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
                        .x(function (d, i) {
                                return x(parseFloat(glob_data[micrograph].MotionCor2.x_shifts[i]));
                        })
                        .y(function (d, i) {
                                return y(parseFloat(glob_data[micrograph].MotionCor2.y_shifts[i]));
                        });
                if (glob_data[micrograph].MotionCor2.x_shifts) {
                        g
                                .append("path")
                                .datum(glob_data[micrograph].MotionCor2.x_shifts)
                                .attr("class", "line motion")
                                .attr("d", line);
                }
        }
}


function create_radial_ctf_plot(micrograph) {
        d3.selectAll("#radial_plot").selectAll(".svg-container").remove();
        var svg = d3.selectAll("#radial_plot")
                .append("div")
                .classed("svg-container", true)
                .classed("ctf", true)
                .append("svg")
                .attr("preserveAspectRatio", "xMinYMin meet")
                .attr("viewBox", "0 0 750 300")
                //class to make it responsive
                .classed("svg-content-responsive", true),
                margin = {
                        top: 20,
                        right: 20,
                        bottom: 30,
                        left: 50
                },
                width = 750 - margin.left - margin.right,
                height = 300 - margin.top - margin.bottom,
                g = svg
                        .append("g")
                        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        if (glob_data[micrograph].Gctf) {
                var x = d3.scaleLinear().rangeRound([width, 0]);

                var y = d3.scaleLinear().rangeRound([height, 0]);
                var back_y = d3.scaleLinear().rangeRound([height, 0]);

                x.domain(d3.extent(glob_data[micrograph].Gctf.EPA.Resolution));
                y.domain(d3.extent(glob_data[micrograph].Gctf.EPA["Sim. CTF"]));
                back_y.domain(d3.extent(glob_data[micrograph].Gctf.EPA["Meas. CTF - BG"]));

                var line = d3
                        .line()
                        .x(function (d, i) {
                                return x(parseFloat(glob_data[micrograph].Gctf.EPA.Resolution[i]));
                        })
                        .y(function (d, i) {
                                return y(parseFloat(glob_data[micrograph].Gctf.EPA["Sim. CTF"][i]));
                        });

                var back_line = d3
                        .line()
                        .x(function (d, i) {
                                return x(parseFloat(glob_data[micrograph].Gctf.EPA.Resolution[i]));
                        })
                        .y(function (d, i) {
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

function setup_canvas(micrograph) {
        var canvas = $('#big_micro_canvas')[0];
        var ctx = canvas.getContext("2d");
        if (glob_data[micrograph].MotionCor2 && glob_data[micrograph].MotionCor2.dimensions) {
                canvas.width = glob_data[micrograph].MotionCor2.dimensions[0];
                canvas.height = glob_data[micrograph].MotionCor2.dimensions[1];
        }
        if (glob_data[micrograph].gautomatch) {
                glob_data[micrograph].gautomatch.map(function (item) {
                        ctx.beginPath();
                        ctx.arc(item.x, item.y, 100, 0, 2 * Math.PI);
                        ctx.lineWidth = 10;

                        // set line color
                        ctx.strokeStyle = '#ff0000';
                        ctx.stroke();
                })
        }
        draw_scalebar(micrograph, ctx);
}

function draw_scalebar(micrograph, ctx) {

        if (HOTSPUR_BASE.glob_data[micrograph].MotionCor2 && HOTSPUR_BASE.glob_data[micrograph].MotionCor2.pixel_size) {
                width = glob_data[micrograph].MotionCor2.dimensions[0];
                height = glob_data[micrograph].MotionCor2.dimensions[1];
                ps = glob_data[micrograph].MotionCor2.pixel_size;
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 30;
                ctx.beginPath();
                ctx.moveTo(width - 50 - 1000 / ps, height - 200);
                ctx.lineTo(width - 50, height - 200);
                ctx.stroke();
                ctx.textAlign = 'center';
                ctx.lineWidth = 10;
                ctx.font = '80px sans';
                ctx.strokeText("100 nm", width - 50 - 500 / ps, height - 50);
        }
}

function setup_micrograph_label(micrograph) {
        $('#micrograph_tag').empty();
        if (glob_annotation[micrograph] && glob_annotation[micrograph].tag) {
                $('#micrograph_tag').append('<div> </div>');
                $('#micrograph_tag').css("text-align", "center");
                var span = $("#micrograph_tag div");
                span.addClass('label');
                span.css("width", "100%");
                switch (glob_annotation[micrograph].tag) {
                        case 'good':
                                span.addClass('label-success');
                                span.text("Good");
                                break;
                        case 'bad':
                                span.addClass('label-danger');
                                span.text("Bad");
                                break;
                        case 'refit':
                                span.addClass('label-warning');
                                span.text("Refit");
                                break;
                }
        }
}


function load_micrograph(micrograph) {
        curr_index = HOTSPUR_BASE.micrograph_time.findIndex(function (d) {
                return d[0] == micrograph;
        });
        if (HOTSPUR_BASE.glob_data[micrograph].MotionCor2) {
                d3
                        .selectAll("#big_micro")
                        .attr("src", "data/" + HOTSPUR_BASE.glob_data[micrograph].MotionCor2.preview_filename);
        } else {
                d3
                        .selectAll("#big_micro")
                        .attr("src", "");
        }
        if (HOTSPUR_BASE.glob_data[micrograph].Gctf) {
                d3
                        .selectAll("#gctf_preview")
                        .attr("src", "data/" + HOTSPUR_BASE.glob_data[micrograph].Gctf.ctf_preview_image_filename);
        } else {
                d3
                        .selectAll("#gctf_preview")
                        .attr("src", "");
        }
        d3.selectAll("#title_field").text(micrograph);
        create_radial_ctf_plot(micrograph);
        create_motion_chart(micrograph);
        create_micrograph_info(micrograph);
        setup_canvas(micrograph);
        setup_micrograph_label(micrograph);
}


var glob_annotation = {};
var user_annotation = {};
var limbo_annotation = {};
var server_annotation = {};
var curr_index;
var glob_data;
var micrograph_time;


function merge_annot() {
        glob_annotation = {};
        for (var micrograph in server_annotation) { glob_annotation[micrograph] = server_annotation[micrograph]; }
        for (var micrograph in limbo_annotation) { glob_annotation[micrograph] = limbo_annotation[micrograph]; }
        for (var micrograph in user_annotation) { glob_annotation[micrograph] = user_annotation[micrograph]; }
}

function sync_annot() {
        if (Object.keys(user_annotation).length() > 0) {
             
        }
}

function previous() {
        if (curr_index > 0)
                load_micrograph(micrograph_time[curr_index - 1][0]);
}

function next() {
        if (curr_index < micrograph_time.length - 1)
                load_micrograph(micrograph_time[curr_index + 1][0]);
}

function set_micrograph_tag(tag) {
        var micrograph = micrograph_time[curr_index][0];
        //HOTSPUT_ANNOTATION.annotate(micrograph, function (ann_obj) {
        //        ann_obj.tag = tag;
        //})
        if (!user_annotation[micrograph]) {
                user_annotation[micrograph] = {};
        }
        user_annotation[micrograph].tag = tag;
        merge_annot();
        setup_micrograph_label(micrograph);
}

Mousetrap.bind('g', function () { set_micrograph_tag('good'); });
Mousetrap.bind('b', function () { set_micrograph_tag('bad'); });
Mousetrap.bind('r', function () { set_micrograph_tag('refit'); });


HOTSPUR_BASE.setup_counter()
HOTSPUR_BASE.setup_navigation(previous, next)
HOTSPUR_BASE.load_data(function () {
        micrograph = HOTSPUR_BASE.findGetParameter("micrograph");
        glob_data = HOTSPUR_BASE.glob_data;
        micrograph_time = HOTSPUR_BASE.micrograph_time;
        if (micrograph == null) {
                if (HOTSPUR_BASE.glob_data[HOTSPUR_BASE.micrograph_time.slice(-1)[0][0]].MotionCor2) {
                        load_micrograph(HOTSPUR_BASE.micrograph_time.slice(-1)[0][0]);
                } else {
                        load_micrograph(HOTSPUR_BASE.micrograph_time.slice(-2)[0][0]);
                }
        } else {
                load_micrograph(micrograph);
        }

});

HOTSPUR_ANNOTATION.load_annotation(function () {
      setup_micrograph_label(micrograph); 
      console.log(HOTSPUR_ANNOTATION.annotation);
})
