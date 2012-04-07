<%inherit file="base.mako"/>

<%def name="header()">
</%def>

<%def name="body()">

<a class="btn" href="${request.route_url('create-scenario')}">Create new scenario</a>
<h3>Existing Scenarios</h3>

<div class="row">
  <div class="span8">
    <table class="zebra-striped">      
      <form method="get" action="${request.route_url('remove-scenarios')}" name="edit">
      <thead>
        <tr>
          <th>#</th>
          <th>Name</th>
          <th>Node count</th>
          <th><button class="btn" type="submit">Delete</button></th>
        </tr>
      </thead>
      <tbody>
        <% from next.model.models import get_cumulative_nodes %>
        % for scenario in scenarios:        
        <tr>
          <td>${scenario.id}</td>
          <td>             
            <a href="${request.route_url('show-phase',id=scenario.id, phase_id=1)}">${scenario}</a>
          </td>
          <td>
           
            ${get_cumulative_nodes(scenario.id, 1).count()}
          </td>
          <td>
            <input name="scenarios" type="checkbox" value="${scenario.id}"/>
          </td>
        </tr>
        % endfor
      </tbody>
      </form>
    </table>
  </div>
</div>

</%def>
