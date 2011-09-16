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
      url: '/scenario/' + options.scenario + '/json',
      format: new OpenLayers.Format.GeoJSON()
      
    })
  });

  map.addLayer(gsat);
  map.addLayer(nodes);
  var bounds = new OpenLayers.Bounds.fromArray(options.bbox);
  map.zoomToExtent(bounds);

};
