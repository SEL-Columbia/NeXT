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
        'scenario': ${scenario.id}
      });
    });

  </script>

</%def>

<%def name="body()">
  <h3>Results for: ${scenario.name}</h3>
  <br />
  <div class="row">
    <div class="span3">
      <a class="btn" href="${request.route_url('remove-scenario',id=scenario.id)}">
         Remove scenario
      </a>
    </div>
    <div class="span3">
      <a href="#" class="btn" id="add-facility">Add new facility</a>
      <a class="btn" id="stop-editing" href="#" style="display:none">Stop editing</a>
    </div>
    <div class="span3">
      <a id="run-scenario" class="btn disabled" href="#">Re-run scenario</a>
    </div>
  </div>
  <hr />
  <div class="row">
    <div id="number-features"
         class="alert-message block-message info span12">
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
    <div class="span-one-third">
      <br />
      <form method="" action="">
        <fieldset>
          <label>Distance</label>
          <input type="text" name="distance" value="" />
        </fieldset>
        <fieldset>
          <input type="submit" name="" value="How many people within"/>
        </fieldset>
      </form>
    </div>
    <div class="span-two-third" id="holder"></div>
  </div>

</%def>
