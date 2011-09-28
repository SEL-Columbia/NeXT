/*
#C7E9B4; #7FCDBB; #41B6C4; #1D91C0; #0C2C84
*/

var load_page = function  (options) {

  (function() { 

    var map = new OpenLayers.Map(
      options.mapDiv, 
      {allOverlays: true, controls: []});
    
    var gsat = new OpenLayers.Layer.Google(
      "Google Satellite",
      {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22}
    ); 

    var gphy = new OpenLayers.Layer.Google(
      "Google Physical",
      {type: google.maps.MapTypeId.TERRAIN, numZoomLevels: 22}
    );

    
    var style = new OpenLayers.Style({
      'stroke': true,
      'stroleColor': '#808080'
    });
  
    var ruleLow = new OpenLayers.Rule({
      filter: new OpenLayers.Filter.Comparison({
        type: OpenLayers.Filter.Comparison.LESS_THAN,
        property: "distance",
        value: 1000,
    }),
      symbolizer: {
        pointRadius: 4, 
        fillColor: "#c7e9b4",
        strokeColor: "black",
        strokeOpacity: 0.2
      }
    });
    
    var ruleMiddle1 = new OpenLayers.Rule({
      filter: new OpenLayers.Filter.Comparison({
        type: OpenLayers.Filter.Comparison.BETWEEN,
        property: "distance",
        lowerBoundary: 1000,
        upperBoundary: 1999
      }),
      symbolizer: {
        pointRadius: 4,
        fillColor: "#7fcdbb",
        strokeColor: "black",
        strokeOpacity: .2
      }
    });

    
    var ruleMiddle2 = new OpenLayers.Rule({
      filter: new OpenLayers.Filter.Comparison({
        type: OpenLayers.Filter.Comparison.BETWEEN,
        property: "distance",
        lowerBoundary: 2000,
        upperBoundary: 3999
      }),
      symbolizer: {
        pointRadius: 4,
        fillColor: "#1D91C0",
        strokeColor: "black",
        strokeOpacity: .2
      }
    });
    
    var ruleHigh = new OpenLayers.Rule({ 
      filter: new OpenLayers.Filter.Comparison({ 
        type: OpenLayers.Filter.Comparison.GREATER_THAN,
        property: "distance",
        value: 4000
    }),
      symbolizer: { 
        pointRadius: 4,
        fillColor: "#0C2C84",
        strokeColor: "black",
        strokeOpacity: .2
      }
    });
    
    style.addRules([ruleLow, ruleMiddle1, ruleMiddle2, ruleHigh]);
    
    var nodes = new OpenLayers.Layer.Vector('nodes', {
      strategies: [new OpenLayers.Strategy.Fixed()],
      styleMap:  style,
      protocol: new OpenLayers.Protocol.HTTP({
        url: options.json_url,
        format: new OpenLayers.Format.GeoJSON()
        
      })
    });

    var fac_style = new OpenLayers.Style({
      pointRadius: 6,
      fillColor: '#5e0f56',
    });

    var fac_nodes = new OpenLayers.Layer.Vector('pop-nodes', { 
      strategies: [new OpenLayers.Strategy.Fixed()],
      styleMap: fac_style,
      protocol: new OpenLayers.Protocol.HTTP({
        url: options.fac_url,
        format: new OpenLayers.Format.GeoJSON()
      })
    });
    
    map.addLayer(gsat);
    map.addLayer(gphy);
    map.addLayer(nodes);
    map.addLayer(fac_nodes);


    var bounds = new OpenLayers.Bounds.fromArray(options.bbox);
    map.zoomToExtent(bounds);
    map.addControl(new OpenLayers.Control.LayerSwitcher());
    map.addControl(new OpenLayers.Control.Navigation());
  }());
  
  /*
  $.getJSON(options.graph_url, function(data){
    var opts = {
    	unit: 'm',
        numBars: 20,
    	//distColors is an optional list of color/value mappings
    	distColors: [
    	//   color, max, description
                ['#c7e9b4', 1000, 'Under 1km'],
                ['#7fcdbb', 2000, 'Under 4km'],
                ['#41b6c4', 3000, 'Under 3km'],
                ['#0c2c84', Infinity, "Greater than 4km"]
    	]
    };
    var distributionData = calculateDistribution(data);
    buildGraph('holder', distributionData, " # People near facilities2", opts);
  });
  */

  $.getJSON(options.graph_cumul_url, function(data){
    var x = 0;

    var xyVals = _.map(data, function(tup) { return [tup[0] * 100, tup[1]]; });
    var maxY = Math.max.apply(null, _.map(data, function(tup) { return tup[1]; }));
    var distColors = [
      //   color, max, description
      ['#c7e9b4', 1000, 'Under 1km'],
      ['#7fcdbb', 2000, 'Under 2km'],
      ['#41b6c4', 3000, 'Under 3km'],
      ['#0c2c84', Infinity, "Under " + (maxY / 1000) + "km"]
   	];

	var r = Raphael('holder');
	r.g.txtattr.font = "12px 'Fontin Sans', Fontin-Sans, sans-serif";
	r.g.text(20, 20, "Meters");
	r.g.text(150, 270, "Population Percent");

    buildLineGraph(r, xyVals, distColors);
    drawLegend(r, distColors, 340, 50);
    //buildLineGraphParts('holder', data, 5);
  });
};
