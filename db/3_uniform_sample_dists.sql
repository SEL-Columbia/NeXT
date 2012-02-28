CREATE OR REPLACE FUNCTION uniform_sample_dists(
  scenario_id integer,
  num_partitions integer)
  RETURNS TABLE (distance integer)
  AS
$$
  SELECT distance FROM
    (SELECT row_num FROM generate_series(
      (SELECT 1), 
      (SELECT count(*) FROM edges WHERE scenario_id=$1),
      (SELECT max(distance) FROM 
        (SELECT 1 distance UNION ALL SELECT count(*) / 
          (SELECT min(ct) FROM (
                SELECT $2 ct UNION ALL 
                SELECT (count(*) - 1) ct FROM edges WHERE scenario_id=$1) num_parts_and_total) 
              num_parts FROM edges
        WHERE scenario_id=$1) one_and_min_parts)) row_num) samples,
     (SELECT row_number() over () row_num, distance FROM
       (SELECT distance FROM edges WHERE scenario_id=$1
        ORDER BY distance) ordered_dists) ordered_dists_row_nums
     WHERE samples.row_num=ordered_dists_row_nums.row_num
$$
LANGUAGE SQL;
