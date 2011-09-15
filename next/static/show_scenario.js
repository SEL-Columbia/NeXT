var load_page = function  (options) {

  region = options.region
  var map = new OpenLayers.Map(options.mapDiv, {allOverlays: true});

  var gsat = new OpenLayers.Layer.Google(
    "Google Satellite",
    {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22}
  ); 


  var nodes = new OpenLayers.Layer.Vector('nodes', {
    strategies: [new OpenLayers.Strategy.Fixed()],
    protocol: new OpenLayers.Protocol.HTTP({
      url: '/scenario/1/json',
      format: new OpenLayers.Format.GeoJSON()
    })
  });

  map.addLayer(gsat);
  map.addLayer(nodes);

};
