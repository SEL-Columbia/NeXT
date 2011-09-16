<%inherit file="base.mako"/>

<%def name="header()">
  <title>Create a new scenario</title>
</%def>

<%def name="body()">
<form 
   method="POST" 
   enctype="multipart/form-data"
   action="${request.route_url('create-scenario')}">

  <fieldset>
    <label>Scenario name</label>
    <input class="xlarge" type="text" name="name" value="" />
  </fieldset>

  <fieldset>
    <label>Population CSV file</label>
    <input type="file" name="pop-csv" value="" />  
  </fieldset>

  <fieldset>
    <label>Facility CSV file </label>
    <input type="file" name="fac-csv" value="" />
  </fieldset>
  
  <input 
     class="btn primary"
     type="submit" 
     name="" 
     value="Upload and run scenario" />
  
</form>

</%def>
