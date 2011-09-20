var map;
var nodes;
var load_page = function  (options) {

  map = new OpenLayers.Map(options.mapDiv, {allOverlays: true});

  var gsat = new OpenLayers.Layer.Google(
      "Google Satellite",
      {type: google.maps.MapTypeId.TERRAIN, numZoomLevels: 22}
  ); 

  var style = new OpenLayers.StyleMap({
      'stroke': true,
      'stroleColor': '#808080'
  });

  var lookup = {    
      'population': {pointRadius: 4 , 'fillColor': '#0069d6'},
      'facility':   {pointRadius: 6, 'fillColor': 'red'}
  }

  style.addUniqueValueRules('default', 'type', lookup);


  nodes = new OpenLayers.Layer.Vector('nodes', {
    strategies: [new OpenLayers.Strategy.Fixed()],
    styleMap:  style,
    protocol: new OpenLayers.Protocol.HTTP({
      url: options.json_url,
      format: new OpenLayers.Format.GeoJSON()
      
    })
  });

  map.addLayer(gsat);
  map.addLayer(nodes);
  var bounds = new OpenLayers.Bounds.fromArray(options.bbox);
  map.zoomToExtent(bounds);


  function graphDistances(elemId, data, title, _opts){
    var opts = _.extend({
    	numBars: 20,
    	defaultColor: 'blue',
    	distColors: false,
    	unit: 'm'
    }, _opts);
    var numBars = opts.numBars,
        unit = opts.unit;

    function textForColumn(col) {
      var stxt = Math.floor(col.start),
      etxt = Math.floor(col.end);
      return "" + stxt + unit + " - " + etxt + unit + ": " + col.value;
    }
    function fin() {
      var barId = this.bar.id - 1,
      current = distributions[barId];
      this.flag = r.g.popup(this.bar.x, this.bar.y, textForColumn(current)).insertBefore(this);
    }
    function fout() {
      this.flag.animate({opacity: 0}, 300, function () {this.remove();});
    }
    var distances = _.map(data, function(arr){return arr[1]}),
    max = _.max(distances),
    min = _.min(distances),
    range = (max-min),
    interval = range / numBars;
    

    var distributions = [];
    for(var i = 0; i < numBars; i++) {
      var start = min + (i * interval);
      var end =  min + ((i + 1) * interval);
      var subset = _.filter(data, function(arr){
	return arr[1] > start && arr[1] < end;
      });
	distributions.push({
	    start: start,
	    end: end,
	    value: subset.length
	});
    }

    var r = Raphael(elemId);
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
	(function drawLegend(){
		var legend = {
				x: 300,
				y: 50,
				fontStyle: "12px 'Fontin Sans', Fontin-Sans, sans-serif",
				padding: 6,
				boxOX: 0,
				boxOY: -4,
				boxW: 10,
				boxH: 10,
				rowHeight: 15
			};
		_.each(colors, function(colD, i){
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
	})();
    }
  };
  
  
  $.getJSON(options.graph_url, function(data){
    var opts = {
    	unit: 'm',
    	numBars: 20,
    	//distColors is an optional list of color/value mappings
    	distColors: [
    	//   color, max, description
                ['green', 1000, "Under 1km"],
                ['orange', 5000, "Under 5km"],
                ['red', Infinity, "Greater than 5km"]
    	]
    };
    graphDistances("holder", data, " # People near facilities", opts);
  
  });
  

};