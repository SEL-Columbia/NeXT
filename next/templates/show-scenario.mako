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
  
  <script 
     type="text/javascript" 
     src="${request.application_url}/static/show_scenario.js">
  </script>

  <script src="${request.application_url}/static/underscore.min.js" 
          type="text/javascript" charset="utf-8">
  </script>

  <script src="${request.application_url}/static/raphael.min.js" 
          type="text/javascript" charset="utf-8">
  </script>

  <script src="${request.application_url}/static/g.raphael-min.js" 
          type="text/javascript" charset="utf-8">
  </script>

  <script src="${request.application_url}/static/g.bar-min.js" 
          type="text/javascript" charset="utf-8">
  </script>
  

  <script type="text/javascript">

    $(function() { 

    load_page({'mapDiv': 'scenario-map', 

      'bbox': ${list(scenario.get_bounds().bounds)},
      'json_url' : '${request.route_url('show-scenario-json', id=scenario.id)}',
      'graph_url': '${request.route_url('graph-scenario', id=scenario.id)}',
      'scenario': ${scenario.id}
    });

    });

  </script>

</%def>

<%def name="body()">
  <h3>Overview for: ${scenario}</h3>

  <br />

  <div id="scenario-map" class="span16" style="height: 400px;padding-top: 10px;">    
  </div>

  <div class="row">
    <div class="span-one-third">,.</div>
    <div class="span-two-third" id="holder"></div>
  </div>

  <table class="zebra-striped">
    <thead>
      <td>From Node</td>
      <td>Distance (Meters)</td>
      <td>To Node</td>
    </thead>
    <tbody>
      % for edge in scenario.get_edges():     
      <tr>
        <td>${edge.from_node}</td>
        <td>${edge.distance}</td>
        <td>${edge.to_node}</td>
      </tr>
     % endfor
  </table>

</%def>
