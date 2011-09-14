<%inherit file="base.mako"/>

<%def name="header()">

  <link 
     rel="stylesheet" 
     href="${request.application_url}/static/openlayers/theme/default/styles.css"
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
     src="${request.application_url}/static/show_region.js">
  </script>
  
  <script type="text/javascript">
    $(function() { 

        show_region({'mapDiv': 'region-map', 'region': ${region.id | u} });

    });
  </script>

</%def>

<%def name="body()">
   <h3>Region: ${region.name}</h3>
   
   
   <div class="row">

     <div class="span8 columns">
       <p>Data points associated with region</p>
       <ul>
       % for node in nodes:
          <li>${node}</li>
       % endfor
       </ul>
     </div>
     
     <div class="span8 columns">
       <div id="region-map"> </div>
     </div>

</%def>
