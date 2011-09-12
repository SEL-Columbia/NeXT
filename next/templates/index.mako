<%inherit file="base.mako"/>

<%def name="header()">

<script type="text/javascript"
        src="${request.application_url}/static/index.js">
</script>

</%def>

<%def name="body()">

<a class="btn" href="#" id="add-new-region">Add a new region</a>

<a class="btn" href="/upload-nodes">Upload new csv file</a>

<h3>Regions</h3>

<ul>
% for region in regions:
  <li><a href="/region/${region.id}">${region}</a></li>
% endfor
</ul>

<div id="add-new-region-form" style="display:none" class="modal">
  <div class="modal-header">
    <h3>Add a new region</h3>
  </div>

  <div class="modal-body">
    <form method="" id="" action="">
      <fieldset>
        <div class="clear-fix">
          <label for="region-name">Region name</label> 
          <div class="input">
            <input id="region-name" 
                   class="xlarge"
                   type="text" 
                   name="name" 
                   value="" />
          </div>
      </div>
      </fieldset>
    </form>
  </div>
  <div class="modal-footer">
    <input type="submit" 
           class="btn primary"
           name="" 
           value="Add new region" />
    <input 
       id="cancel-new-region"
       class="btn secondary"
       type="submit"
       name="" 
       value="Cancel" />
  </div>
  
</div>

<h3>Node types</h3>

<ul>
% for type in types:
  <li>${type}</li>
% endfor

</%def>
