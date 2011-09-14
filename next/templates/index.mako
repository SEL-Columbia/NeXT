<%inherit file="base.mako"/>

<%def name="header()">
</%def>

<%def name="body()">

<a class="btn" href="${request.route_url('create-scenario')}">Create new scenario</a>
<h3>Existing Scenarios</h3>

<ul>
 % for scenario in scenarios:
   <li>
     <a href="${request.route_url('show-scenario',id=scenario.id)}">${scenario}</a>
   </li>
 % endfor
</ul>

</%def>
