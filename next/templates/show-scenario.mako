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
  <script 
     type="text/javascript" 
     src="${request.application_url}/static/prep_scenario.js">
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
        'json_url' : '${request.route_url('show-population-json', id=scenario.id)}',
        'fac_url'  : '${request.route_url('show-facility-json', id=scenario.id)}',
        'graph_url': '${request.route_url('graph-scenario', id=scenario.id)}',
        'new_node_url': '${request.route_url('add-new-nodes', id=scenario.id)}',
        'percent_within': '${request.route_url('find-pop-within', id=scenario.id)}',
        'scenario': ${scenario.id}
      });
    });

  </script>

</%def>

<%def name="body()">
  <h3>Results for: ${scenario.name}</h3>
  <br />
  <div class="row">
    <div class="span8">      

      <a class="btn" href="${request.route_url('remove-scenario',id=scenario.id)}">
        Remove scenario
      </a>
      <a href="#" class="btn" id="add-facility">Add new facility</a>
      <a class="btn" id="stop-editing" href="#" style="display:none">Stop editing</a>
      <a id="run-scenario" class="btn disabled" href="#">Re-run scenario</a>

    </div>
    <div class="span7"> 
      <span id="number-features" 
            class="alert-message success
                   block-message">
      </span>      
    </div>
  </div>
  <br /> 

  <div class="row">
    <div id="scenario-map" 
         class="span16" 
         style="height: 300px;padding-top: 10px;">    

    </div>
  </div>

  <div class="row">
    <div class="span8">
      <br />
      <form method="" action="">
        <p>Percent of population within</p>
        <fieldset>
          <input id="distance" type="text" name="distance" value="1000" />
        </fieldset>
      </form>
      <h2 id="percent"></h2>
    </div>
    <div class="span7" id="holder"></div>
  </div>

</%def>
