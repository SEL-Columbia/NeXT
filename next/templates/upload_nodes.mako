<%inherit file="base.mako"/>

<%def name="header()">
   <title>Please upload a new CSV file</title>
</%def>

<%def name="body()">
  <h2>Upload a new csv file</h2>

  <form method="POST"
        id=""
        action="/upload-nodes" 
        enctype="multipart/form-data">

    <div>
      <select name="node-type">
        % for type in node_types:
              <option value="${type.id}">${type.name}</option>
        % endfor
       </select>
    </div>

    <div>
      <select name='region'>
        % for region in regions:
          <option value="${region.id}">${region.name}</option>
        % endfor
       </select>
    </div>

    <div>
      <input type="file" name="node-file" value="" />
    </div>

    <input class="btn" 
           type="submit" 
           name="submit" 
           value="Upload CSV" />

  </form>

</%def>
