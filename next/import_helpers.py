import csv
import StringIO
from spatial_utils import pg_import

def get_import_spec(input_stream):
    """
    Reads the 1st row of input stream as a csv
    and determines the spec for how to convert to bulk_import csv
    """
    import csv
    x_col = 0
    y_col = 1
    weight_col = 2
    csv_reader = csv.reader(input_stream)
    row0 = csv_reader.next()
    headers = {}
    has_x =  has_y = has_weight = False
    if(len(row0) < 2): 
        raise Exception('Invalid import file')

    for col in range(0, len(row0)):
        val = row0[col]

        if(val in ['longitude', 'Longitude', 'lon', 'Lon', 'x', 'X']):
            has_x = True
            x_col = col
            
        if(val in ['latitude', 'Latitude', 'lat', 'Lat', 'y', 'Y']):
            has_y = True
            y_col = col

        if(val in ['weight', 'Weight', 'population', 'Population', 'pop', 'Pop']):
            has_weight = True
            weight_col = col

    has_header = has_x | has_y
    weight_spec = {'value': 1}
    if(len(row0) > 2 and ((not has_header) or (has_weight))):
        weight_spec = {'column': weight_col}

    #set the input_stream up for processing 
    #(i.e. skip header if it's there)
    input_stream.seek(0)
    if(has_header):
        input_stream.readline()
    return (x_col, y_col), weight_spec


def import_nodes(dbapi_conn, in_node_stream, node_type_id, scenario_id, phase_id):
    """
    Bulk load the nodes from the csv's
    """

    node_stream = StringIO.StringIO()
    importer = pg_import.PGImport(dbapi_conn, 'nodes',
            ('weight', 'node_type_id', 'scenario_id', 'phase_id', 'point'))
    (xy_spec, weight_spec) = get_import_spec(in_node_stream)
    import_specs = {
                    0: weight_spec, 
                    1: {'value': node_type_id}, 
                    2: {'value': scenario_id}, 
                    3: {'value': phase_id}
                   }
    node_translator = pg_import.CSVToCSV_WKT_Point(xy_spec, import_specs)
    #TODO:  may want to move srid to configuration at some point
    node_translator.translate(in_node_stream, node_stream, 4326)
    node_stream.seek(0)
    importer.do_import(node_stream)
            
