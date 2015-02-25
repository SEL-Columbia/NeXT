Data Model
----
* indicates "to do"

"scenario": {
             "id": int,
             "name": string,        // has to be unique
             * "parent_id": int,    // for tracking derivations (forks)
             * "phase": int   // phase 0 for this scenario 
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
                 * "phase_id": int, // ForeignKey
                }
              ]

    * "phase": {
                 "id": int,                   // phase 0 always exists
                 "last_modified" : time,      // 
                 "parent_phase_id" : int,     // ForeignKey
                 "scenario_id": int,          // ForeignKey
               }

    "summary": { 
                  "scenario_id": int, // ForeignKey
                  "phase_id": int, // ForeignKey
                  "average_distance_to_supply_node": float
                  ...
               }

API
---

General Guidelines:
- Follow the routing principles of Rails specified here:
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
      demand-csv:  csv file representing nodes of type "demand" with columns:
                lat, long, weight  (indicated by header row)
      supply-csv:  csv file representing nodes of type "supply" with columns:
                lat, long, weight  (indicated by header row)

   returns:  id: integer (media-type=json) OR show-scenario (media-type=html)

   post-condition(s):  
       1. Scenario has been created
       2. Nearest Neighbor edges have been created

   note:  check for unique name

2. show-scenario: route='/scenarios/:id', request_method='GET'

   params:
       phase=0:  optional end phase number; default = 0
 
   returns:  scenario json representation  (media-type=json) OR 
             html rep (media-type=html)      

3. show-scenarios(list): route='/scenarios', request_method='GET'

   params:
        [name]:  performs a search for scenarios by name
 
   returns:  list of scenario geojson representation (media-type=json) OR
             html rep of list (media-type=html)      
             scenario geometry is simply a list of points as it's BBox
 
4. delete-scenarios: route='/scenarios/delete', request_method='GET'

   params:
       scenarios:  list of scenario ids

   returns:  http status code OR index (media-type=html)

   post-condition(s): all scenarios matching list of id's are
   permanently deleted

5. show-nodes(list): route='/scenarios/:id/phases/:id/nodes', request_method='GET'

   params:
       type:  node type as string (i.e. "demand" or "supply")
       cumulative=TRUE:     cumulative, or just this phases's info? default = cumulative.

   returns:  list of node geojson representations (media-type=json)

6. show-edges: route='/scenarios/:id/phases/:id/', request_method='GET'

   params:
       cumulative=TRUE:     cumulative, or just this phases's info? default = cumulative.

   returns:  list of edge json representations (media-type=json)
  
7. clone-scenario:  route='/scenarios/:id/phases/:id/clone', request_method='GET'

   params:
       [name]:          new name for clone

   returns:  id: integer (media-type=json) OR show-scenario
   (media-type=html)

   post-condition(s):  scenario has been copied (with all phases
   cumulative into a new initial phase on new scenario)

8. create-node(s):  route='/scenarios/:id/phases/:id/node', request_method='POST'
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

9. cover-nodes: route='/scenarios/:id/phases/:id/cover', request_method='POST'

  params:
    method: Name of agglomeration method (i.e. "complete",
    "average"...)
    distance:  Agglomeration cut-off distance
    num_supply_nodes:  Number of supply nodes to add
    number_of_phases_to_split_to: Number of phases to split new service nodes into; default = 1;
                                  if number_of_phases_to_split_to > new nodes, front-load 

  returns:  HTTP Response code OR show-scenario (media-type=html)

  post-condition(s):  
       1. Nodes have been added to the scenario according to the
       params
       2. Nearest Neighbor edges have been created
