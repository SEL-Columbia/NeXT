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


  function graphDistances(elemId, data, numBars, title, unit){
    
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
    max = Math.max.apply(window, distances),
    min = Math.min.apply(window, distances),
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
    r.g.barchart(10, 10, 300, 220, [_.pluck(distributions, 'value')]).hover(fin, fout);
  };
  
  
  $.getJSON(options.graph_url, function(data){

    graphDistances("holder", data, 20, " # People near facilities", "m");
  
  });
  

};
