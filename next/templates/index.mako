<%inherit file="base.mako"/>

<%def name="header()">

</%def>

<%def name="body()">

<a class="btn" href="/add-region">Add a new region</a>

<a class="btn" href="/upload-nodes">Upload new csv file</a>

<h3>Regions</h3>

<ul>
% for region in regions:
  <li><a href="/region/${region.id}">${region}</a></li>
% endfor
</ul>

<h3>Node types</h3>

<ul>
% for type in types:
  <li>${type}</li>
% endfor

</%def>
