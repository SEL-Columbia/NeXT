function show_region(options) {
  region = options.region
  var map = new OpenLayers.Map(options.mapDiv, {allOverlays: true});
  var gsat = new OpenLayers.Layer.Google(
    "Google Satellite",
    {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22}
  ); 
  map.addLayer(gsat);

};

 
