Data Model
----
* indicates "to do"

"scenario": {
             "id": int,
             "name": string,        // has to be unique
             * "parent_id": int,    // for tracking derivations (forks)
             * "stage_ids": [int]   // all stages for which scenario_id = id 
            }

    "node": {
              "id": int,
              "scenario_id": int, // ForeignKey
              "type": string,
              "point": geom,  // as geojson
              "weight": int
             }


     "edge": [
                {
                 "from_node_id": int, // ForeignKey
                 "to_node_id": int, // ForeignKey
                 "scenario_id": int, // ForeignKey
                 "distance": float,
                 * "stage_id": int, // ForeignKey
                }
              ]

    * "stage": {
                 "id": int,          // stage 0 always exists
                 "scenario_id": int, // ForeignKey
               }

    "summary": { 
                  "scenario_id": int, // ForeignKey
                  "stage_id": int, // ForeignKey
                  "average_distance_to_facility": float
                  ...
               }

API
---

General Guidelines:
- Follow the routing principals of Rails specified here:
  http://guides.rubyonrails.org/routing.html
  With the exception that PUT (update) and DELETE are replaced by:
  PUT -> /<noun>/:id/update
  DELETE -> /<noun>/:id/delete

  (Thus, we can't name any entities update or delete :))

- GET's have 2 forms determined by the MIME type of the request:
  XML (which should just be the html view)
  JSON (which should be the entity)
  (see http://zhuoqiang.me/a/restful-pyramid for examples)
  
- Response Codes:  Use HTTP Response codes (but keep it simple)
  i.e. 200 OK, 400 for Bad Request, 404 for NOT FOUND

- Get methods where many items can be returned have the following
  parameters:
  start:  start index in sorted result list (paging)
  end:  end index in sorted result list (paging)

- API Versioning: ?

- Separate urls for map, graph, and textual renditions of a scenario?

- Use full URL to identify entities?

1. create-scenario: route='/scenarios', request_method='POST'
   params:
      pop-csv:  csv file representing nodes of type "population" with columns:
                lat, long, weight  (indicated by header row)
      fac-csv:  csv file representing nodes of type "facility" with columns:
                lat, long  (indicated by header row)

   returns:  id: integer (media-type=json) OR show-scenario (media-type=html)

   post-condition(s):  
       1. Scenario has been created
       2. Nearest Neighbor edges have been created

   note:  check for unique name

2. show-scenario: route='/scenarios/:id', request_method='GET'

   params:
       [stage_start]:  begin stage number
       [stage_end]:  end stage number
 
   returns:  scenario json representation  (media-type=json) OR 
             html rep (media-type=html)      

3. show-scenarios(list): route='/scenarios', request_method='GET'

   params:
        [name]:  performs a search for scenarios by name
 
   returns:  list of scenario json representation (media-type=json) OR
             html rep of list (media-type=html)      
 
4. delete-scenarios: route='/scenarios/delete', request_method='GET'

   params:
       scenarios:  list of scenario ids

   returns:  http status code OR index (media-type=html)

   post-condition(s): all scenarios matching list of id's are
   permanently deleted

5. show-nodes(list): route='/scenarios/:id/nodes', request_method='GET'

   params:
       type:  node type as string (i.e. "population" or "facility")
       [opt] stage_start:  begin stage number
       [opt] stage_end:  end stage number

   returns:  list of node json representations (media-type=json)

6. show-edges: route='/scenarios/:id', request_method='GET'

   params:
       [opt] stage_start:  begin stage number
       [opt] stage_end:  end stage number

   returns:  list of edge json representations (media-type=json)
  
7. clone-scenario:  route='/scenarios/:id/clone', request_method='GET'

   params:
       [name]:  new name for clone

   returns:  id: integer (media-type=json) OR show-scenario
   (media-type=html)

   post-condition(s):  scenario has been copied (with all stages
   merged into a new initial stage)

8. create-node(s):  route='/scenarios/:id/node', request_method='POST'
   ?? Need to think about this ??

   params:
    "nodes": [
              {
               "type": string,
               "point": geom,  // as geojson
               "weight": int
              }
             ]

   returns:  HTTP Response code OR show-scenario (media-type=html)

   post-condition(s):  
       1. Nodes have been added to the scenario
       2. Nearest Neighbor edges have been created

9. cover-nodes: route='/scenarios/:id/cover', request_method='POST'

  params:
    method: Name of agglomeration method (i.e. "complete",
    "average"...)
    distance:  Agglomeration cut-off distance
    num_facilities:  Number of facilities to add
    split_into_stages:  Whether each new facility should be a new stage

  returns:  HTTP Response code OR show-scenario (media-type=html)

  post-condition(s):  
       1. Nodes have been added to the scenario according to the
       params
       2. Nearest Neighbor edges have been created
