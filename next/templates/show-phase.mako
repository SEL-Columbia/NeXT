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
     src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.js">
  </script>

  <script 
     type="text/javascript"
     src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.16/jquery-ui.js">
  </script>

  <script 
     type="text/javascript" 
     src="${request.application_url}/static/bootstrap/bootstrap-tab.js">
  </script>

  <script 
     type="text/javascript" 
     src="${request.application_url}/static/openlayers/OpenLayers.js">
  </script>
  
  <script 
     type="text/javascript" 
     src="${request.application_url}/static/show_phase.js">
  </script>
  <script 
     type="text/javascript" 
     src="${request.application_url}/static/prep_phase.js">
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
    
    /*
    $(function() {
      $('.tabs a:first').tab('show')
    });
    */

    $(function() { 

     load_page({'mapDiv': 'scenario-map', 
        'bbox': ${list(phase.get_bounds().bounds)},
        'demand_url': '${request.route_url('phase-nodes',id=phase.scenario_id,phase_id=phase.id,_query=dict([('type','demand')]))}',
        'supply_url': '${request.route_url('phase-nodes',id=phase.scenario_id,phase_id=phase.id,_query=dict([('type','supply')]))}',
        'graph_cumul_url': '${request.route_url('graph-phase-cumul', id=phase.scenario_id, phase_id=phase.id)}',
        ///'graph_density_url': '${request.route_url('graph-phase', id=phase.scenario_id, phase_id=phase.id)}',
        'new_node_url': '${request.route_url('phase-nodes', id=phase.scenario_id, phase_id=phase.id)}',
        'percent_within': '${request.route_url('find-demand-within', id=phase.scenario_id, phase_id=phase.id)}',
        'create_supply_nodes': '${request.route_url('create-supply-nodes', id=phase.scenario_id, phase_id=phase.id)}',
        'scenario': ${phase.scenario_id},
        'phase': ${phase.id}
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

<!--<div class="container" style="position:absolute;width:120px;height:80%;top:80px;left:40px;background-color:#fff;z-index:99;overflow:auto;">-->
<div class="content" style="position:absolute;width:120px;top:60px;left:20px;background-color:#fff;z-index:99;overflow:auto;">  
  <div class="row" style="margin:1px;">
  <h3>Phases</h3>
  <ul class="nav nav-list">
  <%
    for row in phase_tree_rows:
        row_space = '&nbsp;&nbsp;' * row['cols']
        
        phase_url = request.route_url('show-phase', id=phase.scenario_id, phase_id=row['id'])
        href = "<a href=%s>%s%s</a>" % (phase_url, row_space, row['id'])
        row_str = "<li>%s</li>" % href
        if(phase.id == row['id']):
            row_str = "<li class='active'>%s</li>" % href
            
        context.write(row_str)
  %>
  </ul>
  </div>
</div>

  <h3>Results for: ${phase.scenario.name} ${phase.id}</h3>
  <br />
    <ul class="nav nav-tabs">
      <li class="active"><a href="#auto" data-toggle="tab">Auto</a></li>
      <li><a href="#manual" data-toggle="tab">Manual</a></li>
    </ul>
    <div class="tab-content">
      <div class="tab-pane active" id="auto">
      <!-- <div class="span7"> -->
        <form>
          <div class="row">
          <div class="span2">
  	  <label for="supply_distance">Distance</label>
          </div>
          <div class="span2">
  	  <input type="text" name="supply_distance" id="supply_distance" value="1000" maxlength="10" style="width:60px"/>
          </div>
          <div class="span2">
  	  <label for="num_supply_nodes">Number of Facilities</label>
          </div>
          <div class="span2">
  	  <input type="text" name="num_supply_nodes" id="num_supply_nodes" value="1" maxlength="5" style="width:40px"/>
          </div>
          <div class="span3">
          <a href="#" class="btn" id="auto-add-supply-nodes">Add</a> 
          </div>
          </div>
         </form>
      </div>
      <div class="tab-pane" id="manual">
      <!-- <div class="span7"> -->
        <a href="#" class="btn" id="add-supply-node">Add</a>
        <a class="btn" id="stop-editing" href="#" style="display:none">Finish</a>
        <a id="add-nodes-to-new-phase" class="btn disabled" href="#">Add Nodes to New Phase</a>
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
    <div id="scenario-map" class="span12"
         style="height: 500px;padding-top: 10px;">    
    </div>
  </div>

  <div class="row">
    <div class="span7" style="width: 270px;">
      <br />
        <p>Percent of population within</p>
        <fieldset>
          <input id="distance" type="text" name="distance" value="1000" />
        </fieldset>
      <h2 id="percent"></h2>
    </div>
    <div class="span8" id="holder" style="width: 490px;"></div>
  </div>

</%def>
