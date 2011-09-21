

var load_page = function  (options) {

  (function() { 

    var map = new OpenLayers.Map(options.mapDiv, {allOverlays: true});
    
    var gsat = new OpenLayers.Layer.Google(
      "Google Satellite",
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
        fillColor: "green",
        strokeColor: "black"}
    });
    
    var ruleMiddle = new OpenLayers.Rule({
      filter: new OpenLayers.Filter.Comparison({
        type: OpenLayers.Filter.Comparison.BETWEEN,
        property: "distance",
        lowerBoundary: 1000,
        upperBoundary: 3999
      }),
      symbolizer: {
        pointRadius: 4,
        fillColor: "orange",
        strokeColor: "black"}
    });
    
    var ruleHigh = new OpenLayers.Rule({ 
      filter: new OpenLayers.Filter.Comparison({ 
        type: OpenLayers.Filter.Comparison.GREATER_THAN,
        property: "distance",
        value: 4000
    }),
      symbolizer: { 
        pointRadius: 4,
        fillColor: "red",
        strokeColor: "black"
      }
    });
    
    style.addRules([ruleLow, ruleMiddle]);
    
    var nodes = new OpenLayers.Layer.Vector('nodes', {
      strategies: [new OpenLayers.Strategy.Fixed()],
      styleMap:  style,
      protocol: new OpenLayers.Protocol.HTTP({
        url: options.json_url,
        format: new OpenLayers.Format.GeoJSON()
        
      })
    });
    var fac_style = new OpenLayers.Style({}) ;

    var fac_nodes = new OpenLayers.Layer.Vector('pop-nodes', { 
      strategies: [new OpenLayers.Strategy.Fixed()],
      styleMap: fac_style,
      protocol: new OpenLayers.Protocol.HTTP({
        url: options.fac_url,
        format: new OpenLayers.Format.GeoJSON()
      })
    });

    map.addLayer(gsat);
    map.addLayer(nodes);
    var bounds = new OpenLayers.Bounds.fromArray(options.bbox);
    map.zoomToExtent(bounds);

  })();
  
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
    var distributionData = calculateDistribution(data);
    buildGraph('holder', distributionData, " # People near facilities2", opts);
  });
  

};
