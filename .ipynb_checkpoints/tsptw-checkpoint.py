import gmaps
import googlemaps
import numpy as np
import config as cfg
import json
from ipywidgets.embed import embed_minimal_html
import time
import solver as vsol
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

gmaps.configure(api_key=cfg.PROGRAM.SECRET_KEY)
GG_CLIENT = googlemaps.Client(key=cfg.PROGRAM.SECRET_KEY)
assert GG_CLIENT is not None, "Please check Google API KEY"


class AbstracTSP(object):
    def read(self, input_tsp):
        pass

    def _verify(self):
        return True

    def run(self):
        pass


class TSPTW(AbstracTSP):
    def __init__(self):
        pass

    def read(self, input_tsp):
        self._read_json_from_file(input_tsp)

    def _verify(self):
        return True

    def run(self):
        if self._verify() is True:
            self.metadata = self.data['metadata']
            self.center_point = self.get_center_map(self.data)
            self.depot = [self.get_location(self.get_depot(self.data))]
            self.destinations = [self.get_location(descode) for descode in self.data['destination']]
            self.optimal_tsp = self.find_optimal_tsptw(self.data['depot'], self.destinations, self.data['time_window'])

    def find_optimal_tsptw(self, depot, destinations, time_window):
        logger.info('Gathering distance matrix and duration matrix')
        gg_dist_mat = self.get_google_distance_matrix(destinations, destinations)
        distance_matrix, duration_matrix = self.get_utility_matrices(gg_dist_mat)
        metadata = {'duration_matrix': duration_matrix,
                    'time_window': time_window,
                    'depot': depot}
        problem = vsol.Problem('tsptw', metadata)
        tool = vsol.Solver()
        solution = tool.solve(problem)
        return solution

    @staticmethod
    def get_location(geocode):
        return geocode['geometry']['location']['lat'], geocode['geometry']['location']['lng']

    def _read_json_from_file(self, json_loc):
        logger.info('Reading data from JSON file')
        self.input_tsp = json_loc
        self.data = json.load(open(json_loc, 'r'))

    @staticmethod
    def get_depot(data):
        logger.info('Read depot location')
        depot_idx = data['depot']
        depot = data['destination'][depot_idx]
        return depot

    @staticmethod
    def get_center_map(data):
        lat_locs = [des['geometry']['location']['lat'] for des in data['destination']]
        lng_locs = [des['geometry']['location']['lng'] for des in data['destination']]
        center_lat = np.mean(lat_locs)
        center_lng = np.mean(lng_locs)
        return center_lat, center_lng

    @staticmethod
    def get_google_distance_matrix(origins, destinations, mode='driving'):
        logger.info('Gathering distance matrix and duration matrix')
        return GG_CLIENT.distance_matrix(origins=origins, destinations=destinations, mode=mode)

    @staticmethod
    def parse_into_np_matrix(rows, size, dtype='distance'):
        np_matrix = np.zeros(size)
        for i, row in enumerate(rows):
            for j in range(len(row['elements'])):
                np_matrix[i][j] = row['elements'][j][dtype]['value']
        return np_matrix

    def get_utility_matrices(self, google_matrix):
        if google_matrix['status'] == 'OK':
            size = (len(google_matrix['origin_addresses']), len(google_matrix['destination_addresses']))
            distance_matrix = self.parse_into_np_matrix(google_matrix['rows'], size)
            duration_matrix = self.parse_into_np_matrix(google_matrix['rows'], size, dtype='duration')
            return distance_matrix, duration_matrix
        return None, None


class AbstractVis:
    pass


class TSPTWVis(AbstractVis):
    def __init__(self, tsp_data, figsize=(1400, 800), rps=1.):
        self.tsptw_data = tsp_data
        self.figsize = figsize
        self.rps = rps

    def draw_figure(self, save=True):
        layout = {
            'width': "{}px".format(self.figsize[0]),
            'height': "{}px".format(self.figsize[1]), }
        # Init figure
        fig = gmaps.figure(center=self.tsptw_data.center_point, zoom_level=12, layout=layout)

        # Plot depot with maker layer
        locations = [self.tsptw_data.destinations[route - 1] for route in self.tsptw_data.optimal_tsp]
        labels = [str(i) if i != self.tsptw_data.data['depot'] else 'Depot' for i in
                  range(len(self.tsptw_data.optimal_tsp))]
        makers_layer = gmaps.marker_layer(locations, label=labels)
        fig.add_layer(makers_layer)

        # Plot shorted TSPTW route
        fig = self.add_multiple_directions_layer(fig, locations)
        if save is True:
            self.save_figure_to_html(fig)
        return fig

    def add_multiple_directions_layer(self, fig, locations):
        locations += [locations[0]]
        for i in range(len(locations) - 1):
            route_layer = gmaps.directions_layer(locations[i], locations[i + 1], show_markers=False,
                                                 optimize_waypoints=True)
            # Avoid sending many requests
            time.sleep(self.rps)
            fig.add_layer(route_layer)
        return fig

    @staticmethod
    def save_figure_to_html(fig, output_loc='./output/tsp_vis.html'):
        # Cannot export DirectionLayerView
        embed_minimal_html(output_loc, views=[fig])


if __name__ == '__main__':
    file_data = './sample/tsptw.json'
    tsptw = TSPTW()
    tsptw.read(file_data)
    tsptw.run()
    vis = TSPTWVis(tsptw, rps=0.1)
    vis.draw_figure()
    print('Done')
