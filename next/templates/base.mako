<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>

    <link 
       rel="stylesheet" 
       href="${request.application_url}/static/bootstrap/bootstrap-1.2.0.min.css"
       type="text/css" 
       media="screen" />
    <script 
       type="text/javascript"
       src="${request.application_url}/static/jquery.min.js">
    </script>

    ${self.header()}

  </head>
  <body>

     <div class="container-fluid">

       <h1><a href="/">Modi Labs Spatial Planner</a></h1>
       <hr />
       ${self.body()}

     </div>

  </body>
</html>
