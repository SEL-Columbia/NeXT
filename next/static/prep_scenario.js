function buildLineGraphParts(id, xyVals, numParts) {
	console.log(this, arguments);
	var r = Raphael('holder');
	r.g.txtattr.font = "12px 'Fontin Sans', Fontin-Sans, sans-serif";
	r.g.text(20, 20, "Meters");
	r.g.text(150, 270, "Population Percent");

	var xVals = [];
	var yVals = [];
    
    var tmpXVals = _.map(xyVals, function(tup) { return tup[0]; });
    var tmpYVals = _.map(xyVals, function(tup) { return tup[1]; });

    var end = 1;
    var partSize = Math.ceil(xyVals.length / numParts);
    for(var i = 0; i < numParts; i++) {
        start = end - 1;
        end = start + partSize;
        end = (end > xyVals.length - 1) ? xyVals.length - 1 : end;
        xVals[i] = tmpXVals.slice(start, end);
        yVals[i] = tmpYVals.slice(start, end);
    }
	r.g.linechart(30, 30, 270, 220, xVals, yVals, {shade: true, axis: "0 0 1 1", symbol: "x"});
}

function buildLineGraph(r, xyVals, colorRanges) {

	var xVals = [];
	var yVals = [];
    
    var tmpXVals = _.map(xyVals, function(tup) { return tup[0]; });
    var tmpYVals = _.map(xyVals, function(tup) { return tup[1]; });
    
    var start, end = 1; 
    for(var i = 0; i < colorRanges.length; i++) {
        start = end - 1;
        var upperVal = colorRanges[i][1];
        yVals[i] = _.select(_.rest(tmpYVals, start), function(val) { return val <= upperVal; });
        end = start + yVals[i].length;
        end = (end > xyVals.length) ? xyVals.length: end;
        xVals[i] = tmpXVals.slice(start, end);
    }
    var distColors = _.map(colorRanges, function(tup) { return tup[0]; });
//    console.log(xVals);
//    console.log(yVals);
	r.g.linechart(30, 30, 300, 220, xVals, yVals, {shade: true, axis: "0 0 1 1", symbol: "o", colors: distColors});
}

function drawLegend(r, distColors, x, y) { 
  var legend = {
    x: x,
    y: y,
    fontStyle: "12px 'Fontin Sans', Fontin-Sans, sans-serif",
    padding: 6,
    boxOX: 0,
    boxOY: -4,
    boxW: 10,
    boxH: 10,
    rowHeight: 15
  };
  _.each(distColors, function(colD, i){
    var col = colD[0],
   	value = colD[1],
   	description = colD[2];
   	var rowY = legend.y + legend.rowHeight * i;
   	r.rect(legend.x + legend.boxOX, rowY + legend.boxOY, legend.boxW, legend.boxH)
        .attr({
          fill: col,
          'stroke-opacity': 0.3
         });
    r.text(legend.x + legend.boxOX + legend.boxW + legend.padding, rowY, description)
      .attr('text-anchor', 'start')
      .attr('font', legend.fontStyle);
    });
}

function calculateDistribution(rawData, _opts) {
    var opts = _.extend({
        numBars: 20
    }, _opts);
    
    var distances = _.map(rawData, function(arr){return arr[1]}),
        max = _.max(distances),
        min = _.min(distances),
        range = (max-min),
        interval = range / opts.numBars;
    var distributions = [];
    for(var i = 0; i < opts.numBars; i++) {
        var start = min + (i * interval);
        var end =  min + ((i + 1) * interval);
        var subset = _.filter(rawData, function(arr){
            return arr[1] > start && arr[1] < end;
        });
    	distributions.push({
    	    start: start,
    	    end: end,
    	    value: subset.length
    	});
    }
    return distributions;
}


function buildGraph(id, distributions, title, _opts) {

    var opts = _.extend({
    	numBars: 20,
    	defaultColor: 'blue',
    	distColors: false,
    	unit: 'm'
    }, _opts);
    var numBars = opts.numBars,
        unit = opts.unit;
    var graphElem = $('#'+id);
    function textForColumn(col) {
        var stxt = Math.floor(col.start),
        etxt = Math.floor(col.end);
        return "" + stxt + unit + " - " + etxt + unit + ": " + col.value;
    }
    function fin() {
      var barId = this.bar.id - 1;
      var current = distributions[barId];
      this.flag = r.g.popup(this.bar.x, this.bar.y, textForColumn(current)).insertBefore(this);
    }
    function fout() {
      this.flag.animate({opacity: 0}, 300, function () {this.remove();});
    }
    var r = Raphael(id);
    r.g.txtattr.font = "12px 'Fontin Sans', Fontin-Sans, sans-serif";
    r.g.text(160, 10, title);
    var gOpts = {colors: [opts.defaultColor]};
    var bc = r.g.barchart(10, 10, 300, 220, [_.pluck(distributions, 'value')], gOpts).hover(fin, fout);
    if(!!opts.distColors) {
        var colors = _.map(distributions, function(d, i){
            var dcMatch = _.detect(opts.distColors, function(a){ return d.end < a[1] });
            return dcMatch!==undefined ? dcMatch[0] : opts.defaultColor;
        });
    	//bars are buried in the raphael object... AFAICT
    	var bars = bc.bars.items[0].items;
    	_.each(colors, function(c, i){
    	    bars[i].attr('fill', c);
    	});
        drawLegend(_opts.distColors, 300, 50);
    }
}
//"holder", distributionData, " # People near facilities", opts



function log() {
	if(console !== undefined && console.log !== undefined) {
		console.log.apply(console, arguments);
	}
}
function warn() {
	if(console !== undefined && console.warn !== undefined) {
	    console.warn.apply(console, arguments);
	    throw(arguments[0]);
	}
}
