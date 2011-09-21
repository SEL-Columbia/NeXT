<%inherit file="base.mako"/>

<%def name="header()">
  <link 
     rel="stylesheet" 
     href="${request.application_url}/static/openlayers/theme/default/style.css"
     type="text/css" 
     media="screen" />

  <script 
     type="text/javascript"
     src="http://maps.google.com/maps/api/js?sensor=false">
  </script>

  <script 
     type="text/javascript" 
     src="${request.application_url}/static/openlayers/OpenLayers.js">
  </script>
  
  <script type="text/javascript">
    $(function() { 

        var map = new OpenLayers.Map(
            'map', 
            { allOverlays: true,
              controls: []
            }
        );
        
        var gphy = new OpenLayers.Layer.Google(
            "Google Physical",
            {type: google.maps.MapTypeId.TERRAIN, numZoomLevels: 22}
        );
        map.addLayer(gphy);

        var style = new OpenLayers.Style({ 
            fillColor: 'black',
            strokeWidth: 5
        });

        var scs = new OpenLayers.Layer.Vector('Scenairos', { 
            strategies: [new OpenLayers.Strategy.Fixed()],
            styleMap: style,
            protocol: new OpenLayers.Protocol.HTTP({
                url: '${request.route_url('show-all-scenarios')}',
                format: new OpenLayers.Format.GeoJSON()
            })
        });

        map.addLayer(scs);
        map.addControl(new OpenLayers.Control.LayerSwitcher());
        map.addControl(new OpenLayers.Control.Navigation());
        map.setCenter(new OpenLayers.LonLat(10.2, 48.9), 5);
    });
  </script>

</%def>

<%def name="body()">

<a class="btn" href="${request.route_url('create-scenario')}">Create new scenario</a>
<h3>Existing Scenarios</h3>

<div class="row">
  <div class="span8">
    <table>      
      <thead>
        <td>Name</td>
      </thead>
      <tbody>
        % for scenario in scenarios:        
        <tr>
          <td> 
            <a href="${request.route_url('show-scenario',id=scenario.id)}">${scenario}</a>
          </td>
        </tr>
        % endfor
      </tbody>
    </table>
  </div>
  <div class="span8"> 
    <div id="map" style="height:400px;">
    </div>
  </div>
</div>

</%def>
