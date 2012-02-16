Data
----

"scenario": {"id": Int,
             "name": String,                                    // has to be unique
             "parent_id": Int,                                  // for tracking derivations
             "stage_ids": [Int]                                 // all stages for which scenario_id = id 
            }
    "population_point" : {"id": Int,
                      "scenario_id": Int / ForeignKey,
                      "geom": Point,
                      "population": int
             }
    "stage": {"id": Int,                                // stage 0 always exists
              "scenario_id": Int,
             }
        "facility" : {"id": Int,
                      "scenario_id": Int / ForeignKey,
                      "stage_id": Int / ForeignKey,                     //0 for facilities input initially
                      "geom": Point,
                     } 
        "nearest_neighbor_info" : [{"facility_id": Int / ForeignKey,
                                    "scenario_id": Int / ForeignKey,
                                    "stage_id": Int / ForeignKey,
                                    "population_id": Int / ForeignKey,
                                    "distance": Float
                                   }]
        "summary" : { "scenario_id": Int / ForeignKey,
                      "stage_id": Int / ForeignKey,
                      "average_distance_to_facility": Float
                      ..
                    }

API
---


1. /createScenario
Post Inputs: ScenarioName: string
             facilityCsv: CSV file, with "lat", "long" columns
             populationCsv: CSV files, with columns: "lat", "long", [optional: "population"]
Side-Effects (async): (1) Creates Scenario in DB
                      (2) Do the Nearest Neighbor calculations
Return: UniqueScenarioName (string) -- same as ScenarioName if no conflicts; different if there are conflicts

2. /deleteScenarios
Post Inputs: ScenarioNames: [string]
Side-Effects (asynch): (1) Deletes all Scenarios in list from DB

3. /getScenario
Post Inputs: ScenarioName: string
             stages: [stage_id]
Outputs: [stage_json] 
          
          stage_json = {"id": Int, "scenario_id": Int / ForeignKey,
                        "scenario_name": string,            //scenario_name == ScenarioName
                        "newfacilities" : [facility]        //facility.stage_id = "id" and facility.scenario_id==ScenarioName
                        "nnInfo" : [nearest_neighbor_edge]  //nnedge.stage_id == "id" and nnedge.scenario_id=="scenario_id"]}

4. /getScenarioList
Post Inputs: NULL
Outputs: [scenario]

5. /cloneScenartio
Post Inputs: scenario_name : string
             new_scenario_name : string
Side-Effects: see (1); new_scenario's parent id is scenario_name's id
Outputs: new_scenario_unique_name

6. /addFacilities
Post Inputs: scenario_name: string
             method: {"name": "by_coverage_distance",       // only one method supported for now
                      "params": {"dist": Int, "N": Int}} 
[opt]        split_into_n_stages: Int                                    // default = 1
[opt]        staging_method: {"name": "maximize_coverage",  // only one method supported for now
                              "params": {}}
Ouputs: [stage_json]
