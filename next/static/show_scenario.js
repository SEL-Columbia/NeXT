/*
#C7E9B4; #7FCDBB; #41B6C4; #1D91C0; #0C2C84
*/
var new_nodes;

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
      'strokeColor': '#808080'
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
        upperBoundary: 2999
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
        value: 2999
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
        url: options.pop_url,
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
    map.addControl(new OpenLayers.Control.MousePosition());

    // new layer to allow users to add new points
    new_nodes = new OpenLayers.Layer.Vector();
    map.addLayer(new_nodes);

    // add control to allow users to add a new point

    var edit_control = new OpenLayers.Control.DrawFeature(
      new_nodes,
      OpenLayers.Handler.Point
    ); 
    
    map.addControl(edit_control);

    /*
    function update_feature_counter(event) { 
      var number = new_nodes.features.length;
      console.log(number);
      $('#number-features').html('You have added ' + number + ' node(s) to your facilities');
    };
    
    new_nodes.events.on({ 
      sketchcomplete: update_feature_counter
    })
    */

    var stop = $('#stop-editing');
    var edit = $('#add-facility');
    var run  = $('#run-scenario');
    var auto_add  = $('#auto-add-facilities');

    edit.click(function() {
      edit_control.activate();
      $(this).css('display', 'none') ; 
      stop.css('display', 'inline');
      
    });

    stop.click(function() { 
      $(this).css('display', 'none');
      edit.css('display', 'inline');
      edit_control.deactivate(); 
      
      if (new_nodes.features.length !==0 ) {         
        $('#run-scenario').removeClass('disabled');        
      }      
    });
    
    run.click(function() { 
      var runp = confirm('Re-running will delete your original data, still re-run?');
      if (runp) {  
        // steps
        // sync new data with old facility datasets via post
        // call the run url for the scenario
        // route user to new scenario page.
        var facilities = _.map(
          new_nodes.features, 
          function(feature) { 
            var geometry = feature.geometry.transform(
              new OpenLayers.Projection('EPSG:900913'),
              new OpenLayers.Projection('EPSG:4326')
            );
            
            var geoJSON = new OpenLayers.Format.GeoJSON();
            point = geoJSON.extract.point(geometry);
            return { 'type': 'Features', 
                     'geometry': {
                         'type': 'Point', 
                         'coordinates': point
                      }, 
                     'properties': {
                          'type': 'facility',
                          'weight': 1
                     }
                   }
                  
            // return {x: geometry.x, y: geometry.y};            
          }
        )

        var features = {'features': facilities }
        $.ajax({
          type: 'POST',
          url: options.new_node_url,
          data: JSON.stringify(features),
          contentType: 'application/json; charset=utf-8',
          success: function(data) { 
            window.location = '/scenarios/' + options.scenario;
          },         
        });
      } else { 
        // do nothing
      }
     
    });

    auto_add.click(function() { 
        $.ajax({
            type: 'POST',
            url: options.create_facilities,
            data: JSON.stringify({'d': $('#facility_distance').val(),
                                  'n': $('#num_facilities').val()}),
            contentType: 'application/json; charset=utf-8',
            success: function(data) { 
                window.location = '/scenarios/' + options.scenario;
            }
        });
    });

    /*
    $( "#auto-add-form" ).dialog({
			autoOpen: false,
			height: 300,
			width: 350,
			modal: true,
			buttons: {
	            "Add Facilities": function() {
                $.ajax({
                type: 'POST',
                url: options.new_node_url,
                data: JSON.stringify(features),
                contentType: 'application/json; charset=utf-8',
                success: function(data) { 
                window.location = '/scenario/' + options.scenario + '/run' ;
                },         
                });
				},
				Cancel: function() {
					$( this ).dialog( "close" );
				}
			},
			close: function() {
                $(this).dialog("close");
		    }
      });

      $("#auto-add-facilities")
        .button()
        .click(function() { 
          $("#auto-add-form").dialog("open");
        });
      */
    
  }());


  function find_percent_within() { 
//   --not using this txt yet.
//    var txt = "% people within";
    $.ajax({
      type: 'POST',
      url: options.percent_within,
      data: JSON.stringify({'d': $('#distance').val() }),
      contentType: 'application/json; charset=utf-8',
      success: function(data) { 
        var pct = Math.floor((data.total * 10000) / 100);
        $('#percent').text("" + pct + "%");
      }
      
    })
    
  }; 

  find_percent_within();
  $('#distance').change(function() { 
    find_percent_within();
  })

  
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
    //don't do anything if there's no data
    if(data.length == 0) {
      return;
    }
    var x = 0;

    var xyVals = _.map(data, function(tup) { return [tup[0], tup[1] * 100]; });
    var maxX = Math.max.apply(null, _.map(data, function(tup) { return tup[0]; }));
    var formattedMaxX = Math.floor((maxX / 1000) * 100) / 100;
    var distColors = [
      //   color, max, description
      ['#c7e9b4', 1000, 'Under 1km'],
      ['#7fcdbb', 2000, 'Under 2km'],
      ['#41b6c4', 3000, 'Under 3km'],
      ['#0c2c84', Infinity, "Under " + formattedMaxX + "km"]
    ];

    var r = Raphael('holder');
    r.g.txtattr.font = "12px 'Fontin Sans', Fontin-Sans, sans-serif";
    r.g.text(40, 20, "% Population");
    r.g.text(200, 270, "Distance (meters)");
    
    //buildLineGraph(r, xyVals);
    buildLineGraph(r, xyVals, distColors);
    drawLegend(r, distColors, 360, 50);
    //buildLineGraphParts(r, xyVals, 5);
  });


  $.getJSON(options.graph_density_url, function(data){
    //don't do anything if there's no data
    if(data.length == 0) {
      return;
    }
    var x = 0;

    var xyVals = _.map(data, function(tup) { return [tup[0], tup[1] * 100]; });
    var maxX = Math.max.apply(null, _.map(data, function(tup) { return tup[0]; }));
    var formattedMaxX = Math.floor((maxX / 1000) * 100) / 100;
    var distColors = [
      //   color, max, description
      ['#c7e9b4', 1000, 'Under 1km'],
      ['#7fcdbb', 2000, 'Under 2km'],
      ['#41b6c4', 3000, 'Under 3km'],
      ['#0c2c84', Infinity, "Under " + formattedMaxX + "km"]
    ];

    var r = Raphael('holder');
    
    //buildLineGraph(r, xyVals);
    buildLineGraph(r, xyVals, distColors);
    //buildLineGraphParts(r, xyVals, 5);
  });

};
