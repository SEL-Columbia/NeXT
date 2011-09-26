<!DOCTYPE html>
<html lang="en">
  <head>

    <link 
       rel="stylesheet" 
       href="${request.application_url}/static/bootstrap/bootstrap-1.2.0.min.css"
       type="text/css" 
       media="screen" />
    <link 
       rel="stylesheet" 
       href="${request.application_url}/static/custom.css"
       type="text/css" 
       media="screen" />

    <script 
       type="text/javascript"
       src="${request.application_url}/static/jquery.min.js">
    </script>

    ${self.header()}

  </head>
  <body>

     <div class="container">
       <div class="content">
         <h1><a href="${request.application_url}">NeXT</a></h1>
         <hr />
         ${self.body()}         
       </div>
     </div>

  </body>
</html>
