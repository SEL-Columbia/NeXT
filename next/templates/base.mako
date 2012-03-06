<!DOCTYPE html>
<html lang="en">
  <head>
    
    <link rel="stylesheet"
          href="${request.application_url}/static/bootstrap/bootstrap.min.css"
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
    <div class="topbar">
      <div class="topbar-inner"> 
        <div class="container"> 
          <h1><a class="brand" href="${request.application_url}">Modi Labs Spatial
          Planning Tool</a></h1>
        </div>
      </div>

    </div>    
     <div class="container">
       <div class="content">
         ${self.body()}         
       </div>
     </div>

  </body>
</html>
