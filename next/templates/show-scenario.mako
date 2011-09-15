<%inherit file="base.mako"/>

<%def name="header()">
</%def>

<%def name="body()">
  <h3>Overview for: ${scenario}</h3>
  
  <a class="btn primary" 
     href="${request.route_url('run-scenario', id=scenario.id)}">Run Scenario</a>

  <ul>
  % for node in nodes:
    <li>${node}</li>
  % endfor
  </ul>

</%def>
