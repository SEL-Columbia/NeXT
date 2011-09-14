<%inherit file="base.mako"/>

<%def name="header()">
</%def>

<%def name="body()">
  <h3>Overview for: ${scenario}</h3>

  <ul>
  % for node in nodes:
    <li>${node}</li>
  % endfor
  </ul>

</%def>
