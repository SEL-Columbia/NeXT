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
     src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.16/jquery-ui.js">
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

  <script src="${request.application_url}/static/g.line-min.js" 
          type="text/javascript" charset="utf-8">
  </script>
  

  <script type="text/javascript">

    $(function() { 


     load_page({'mapDiv': 'scenario-map', 
        'bbox': ${list(scenario.get_bounds().bounds)},
        'json_url' : '${request.route_url('show-population-json', id=scenario.id)}',
        'fac_url'  : '${request.route_url('show-facility-json', id=scenario.id)}',
        'graph_cumul_url': '${request.route_url('graph-scenario-cumul', id=scenario.id)}',
        //'graph_url': '${request.route_url('graph-scenario', id=scenario.id)}',
        'new_node_url': '${request.route_url('add-new-nodes', id=scenario.id)}',
        'percent_within': '${request.route_url('find-pop-within', id=scenario.id)}',
        'create_facilities': '${request.route_url('create-facilities', id=scenario.id)}',
        'scenario': ${scenario.id}
      });
    });

  </script>

</%def>

<%def name="body()">
<div id="auto-add-form" title="Enter Parameters">
    <!--
	<p class="validateTips">All form fields are required.</p> 
    -->
</div>

  <h3>Results for: ${scenario.name}</h3>
  <br />

  <div class="row">
    <div class="span7">      
         
    <a href="#" class="btn" id="auto-add-facilities">Auto-add new facilities</a> 
	  <form>
      	  <fieldset>
	      <label for="facility_distance">Distance</label>
	      <input type="text" name="facility_distance" id="facility_distance" value="1000" class="text ui-widget-content ui-corner-all" />
	      <label for="num_facilities">Number of Facilities</label>
	      <input type="text" name="num_facilities" id="num_facilities" value="1" class="text ui-widget-content ui-corner-all" />
      	  </fieldset>
	  </form>

    </div>
    <div class="span7"> 
      <a href="#" class="btn" id="add-facility">Manually add new facility</a>
      <a class="btn" id="stop-editing" href="#" style="display:none">Stop editing</a>
      <a id="run-scenario" class="btn disabled" href="#">Re-run scenario</a>
      <!--
      <span id="number-features" 
            class="alert-message success
                   block-message">
      </span>      
      -->
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
    <div class="span8" style="width: 270px;">
      <br />
      <form method="" action="">
        <p>Percent of population within</p>
        <fieldset>
          <input id="distance" type="text" name="distance" value="1000" />
        </fieldset>
      </form>
      <h2 id="percent"></h2>
    </div>
    <div class="span7" id="holder" style="width: 470px;"></div>
  </div>

</%def>
