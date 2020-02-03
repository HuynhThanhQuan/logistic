from __future__ import print_function
from IPython.display import display
import os
import matplotlib.pyplot as plt
import gmaps
import googlemaps
import argparse
import numpy as np
import pandas as pd
import json
from ipywidgets.embed import embed_minimal_html
import time
import tsplib95
import networkx as nx
import scipy
import os
import subprocess
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Problem:
    def __init__(self, prob_type, metadata):
        self.prob_type = prob_type
        self.metadata = metadata


class ORTool:
    def __init__(self, settings=None):
        self.settings = settings

    def solve(self, problem):
        if problem.prob_type == 'tsp':
            return self.find_tsp_solution(problem.metadata)

    def find_tsp_solution(self, metadata):
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]

        def output_solution(manager, routing, assignment):
            index = routing.Start(0)
            route = []
            route_distance = 0
            while not routing.IsEnd(index):
                route += [manager.IndexToNode(index)]
                previous_index = index
                index = assignment.Value(routing.NextVar(index))
            return route

        distance_matrix = metadata['distance_matrix']
        depot = metadata.get('depot', 0)
        num_vehicles = metadata.get('num_vehicles', 1)
        manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicles, depot)
        routing = pywrapcp.RoutingModel(manager)
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        assignment = routing.SolveWithParameters(search_parameters)
        if assignment:
            route = output_solution(manager, routing, assignment)
            return route
        return None


class LKH:
    def __init__(self, settings=None):
        self.settings = settings

    def solve(self, problem):
        if problem.prob_type == 'tsptw':
            return self.find_tsptw_solution(problem.metadata)

    def find_tsptw_solution(self, metadata):
        tsp_filename = self.write_tsplib95_format(
            duration_matrix=metadata['duration_matrix'],
            time_window=metadata['time_window'],
            depot=metadata['depot'])
        par_filename = self.write_par_file()
        return self.execute_cmd(par_filename)

    def execute_cmd(self, par_filename):
        result = subprocess.run(['../solver/LKH-3.0.6/LKH', '{}'.format(par_filename)], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        #         for l in result.stdout.decode("utf-8") .split('\n'):
        #             print(l)
        #         for l in result.stderr.decode("utf-8") .split('\n'):
        #             print(l)
        if os.path.exists('../tsplib95/problem.sol'):
            sol = tsplib95.load_solution('../tsplib95/problem.sol')
            return sol.tours[0]

    def write_par_file(self):
        filename = '../tsplib95/problem.par'
        file = open(filename, 'w')
        file.write('PROBLEM_FILE = {}\n'.format('../tsplib95/problem.tsptw'))
        # file.write('MAX_TRIALS = {}\n'.format('5'))
        # file.write('RUNS = {}\n'.format('10'))
        file.write('TOUR_FILE = {}\n'.format('../tsplib95/problem.sol'))
        # file.write('TRACE_LEVEL = {}\n'.format('0'))
        file.close()
        return filename

    def write_tsplib95_format(self, **kwargs):
        filename = '../tsplib95/problem.tsptw'
        file = open(filename, 'w')
        file.write('NAME : {}\n'.format('problem.tsptw'))
        file.write('TYPE : {}\n'.format('TSPTW'))
        file.write('DIMENSION : {}\n'.format(len(kwargs['duration_matrix'])))
        file.write('EDGE_WEIGHT_TYPE : {}\n'.format('EXPLICIT'))
        file.write('EDGE_WEIGHT_FORMAT : {}\n'.format('FULL_MATRIX'))
        file.write('EDGE_WEIGHT_SECTION\n')
        for arr in kwargs['duration_matrix']:
            file.write(' '.join([str(int(e)) for e in arr]) + '\n')
        file.write('TIME_WINDOW_SECTION\n')
        for i, arr in enumerate(kwargs['time_window']):
            file.write(str(i + 1) + ' ' + ' '.join([str(e) for e in arr]) + '\n')
        file.write('DEPOT_SECTION\n')
        file.write(str(kwargs.get('depot', 0) + 1) + '\n')
        file.write('-1\n')
        file.write('EOF')
        file.close()
        return filename


# assert os.getenv('GOOGLE_API_KEY') is not None, "Please check environment variables"
os.environ['GOOGLE_API_KEY'] = 'AIzaSyAQWqMTOcyLBRDR2skO4F_5QEWzNDOlUHw'
gmaps.configure(api_key=os.getenv('GOOGLE_API_KEY'))
GG_CLIENT = googlemaps.Client(key=os.getenv('GOOGLE_API_KEY'))
assert GG_CLIENT is not None, "Please check Google API KEY"


class AbstracTSP(object):
    def read(self):
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
            self.addresses = [self.get_address(descode) for descode in self.data['destination']]
            self.center_point = self.get_center_map(self.data)
            self.convered_point = self.get_covered_point(self.data)
            self.depot = [self.get_location(self.get_depot(self.data))]
            self.destinations = [self.get_location(descode) for descode in self.data['destination']]
            self.optimal_tsp = self.find_optimal_tsptw(self.data['depot'], self.destinations, self.data['time_window'])
            self.descriptions = self.get_direction_description(self.optimal_tsp)

    def get_address(self, geocode):
        return geocode['formatted_address']

    def find_optimal_tsptw(self, depot, destinations, time_window):
        logger.info('Gathering distance matrix and duration matrix')
        #         gg_dist_mat = self.get_google_distance_matrix(destinations, destinations)
        distance_matrix, duration_matrix = self.get_utility_matrices(destinations, destinations)
        metadata = {'duration_matrix': duration_matrix,
                    'time_window': time_window,
                    'depot': depot}
        problem = Problem('tsptw', metadata)
        tool = LKH()
        solution = tool.solve(problem)
        return solution

    def get_location(self, geocode):
        return (geocode['geometry']['location']['lat'], geocode['geometry']['location']['lng'])

    def _read_json_from_file(self, json_loc):
        logger.info('Reading data from JSON file')
        self.input_tsp = json_loc
        self.data = json.load(open(json_loc, 'r'))

    def get_depot(self, data):
        logger.info('Read depot location')
        depot_idx = data['depot']
        depot = data['destination'][depot_idx]
        return depot

    def get_center_map(self, data):
        lat_locs = [des['geometry']['location']['lat'] for des in data['destination']]
        lng_locs = [des['geometry']['location']['lng'] for des in data['destination']]
        center_lat = np.mean(lat_locs)
        center_lng = np.mean(lng_locs)
        return center_lat, center_lng

    def get_covered_point(self, data):
        lat_locs = [des['geometry']['location']['lat'] for des in data['destination']]
        lng_locs = [des['geometry']['location']['lng'] for des in data['destination']]
        convered_lat = np.min(lat_locs) + ((np.max(lat_locs) - np.min(lat_locs)) / 2)
        convered_lng = np.min(lng_locs) + ((np.max(lng_locs) - np.min(lng_locs)) / 2)
        return convered_lat, convered_lng

    def parse_into_np_matrix(self, rows, size, dtype='distance'):
        np_matrix = np.zeros(size)
        for i, row in enumerate(rows):
            for j in range(len(row['elements'])):
                np_matrix[i][j] = row['elements'][j][dtype]['value']
        return np_matrix

    def get_matrix(self, google_matrix):
        if google_matrix['status'] == 'OK':
            size = (len(google_matrix['origin_addresses']), len(google_matrix['destination_addresses']))
            distance_matrix = self.parse_into_np_matrix(google_matrix['rows'], size)
            duration_matrix = self.parse_into_np_matrix(google_matrix['rows'], size, dtype='duration')
            return (distance_matrix, duration_matrix)
        return (None, None)

    def get_utility_matrices(self, origins, destinations, mode='driving'):
        logger.info('Gathering distance matrix and duration matrix')
        if 'datetime' in self.metadata.keys():
            self.time_marker = time.mktime(time.strptime(self.metadata['datetime'], "%d/%m/%Y %H:%M:%S"))
        else:
            self.time_marker = time.mktime(time.localtime(time.time()))

        # Get google matrix
        if len(origins) * len(destinations) < 100:
            gg_mat = GG_CLIENT.distance_matrix(origins=origins, destinations=destinations, mode=mode)
            return self.get_matrix(gg_mat)
        else:
            dist = None
            dura = None
            for i, origin in enumerate(origins):
                gg_matrix = GG_CLIENT.distance_matrix(origins=origin, destinations=destinations, mode=mode)
                distance_matrix, duration_matrix = self.get_matrix(gg_matrix)
                if i == 0:
                    dist = distance_matrix
                    dura = duration_matrix
                else:
                    dist = np.concatenate((dist, distance_matrix), axis=0)
                    dura = np.concatenate((dura, duration_matrix), axis=0)
            return dist, dura

    def get_direction_description(self, tour):
        if tour is not None:
            descriptions = []
            for i in range(len(tour) - 1):
                origin = self.get_location(self.data['destination'][tour[i] - 1])
                target = self.get_location(self.data['destination'][tour[i + 1] - 1])
                directions_result = GG_CLIENT.directions(origin, target, mode="driving", )
                descriptions.append(directions_result)
            origin = self.get_location(self.data['destination'][tour[-1] - 1])
            target = self.get_location(self.data['destination'][tour[0] - 1])
            directions_result = GG_CLIENT.directions(origin, target, mode="driving", )
            descriptions.append(directions_result)
            return descriptions
        return None


class AbstractVis:
    def __init__(self, tsp_data):
        pass


class TSPTWVis(AbstractVis):
    def __init__(self, tsptw_data, figsize=(1400, 800), rps=1):
        self.tsptw_data = tsptw_data
        self.figsize = figsize
        self.rps = rps

    def draw_figure(self, save=True):
        layout = {
            'width': "{}px".format(self.figsize[0]),
            'height': "{}px".format(self.figsize[1]), }
        # Init figure
        fig = gmaps.figure(center=(self.tsptw_data.convered_point), zoom_level=13, layout=layout)

        # Plot depot with maker layer
        locations = [self.tsptw_data.destinations[route - 1] for route in self.tsptw_data.optimal_tsp]
        labels = [str(i) if i != self.tsptw_data.data['depot'] else 'Depot' for i in
                  range(len(self.tsptw_data.optimal_tsp))]
        info_box_contents = []
        for idx in self.tsptw_data.optimal_tsp:
            address = self.tsptw_data.addresses[idx - 1]
            tw = self.tsptw_data.data['time_window'][idx - 1]
            time_marker = self.tsptw_data.time_marker
            opened_tw = time.strftime("%d/%m/%y %H:%M:%S", time.localtime(time_marker + tw[0]))
            closed_tw = time.strftime("%d/%m/%y %H:%M:%S", time.localtime(time_marker + tw[1]))
            content = """
            <div class="poi-info-window gm-style"> 
            <div jstcache="126" class="title full-width" jsan="7.title,7.full-width">{}</div>
            <div jstcache="127" jsinstance="1" class="address-line full-width" jsan="7.address-line,7.full-width">Open: {}</div>
            <div jstcache="127" jsinstance="1" class="address-line full-width" jsan="7.address-line,7.full-width">Close: {}</div>
            </div>""".format(address, opened_tw, closed_tw)
            info_box_contents.append(content)
        makers_layer = gmaps.marker_layer(locations, label=labels, info_box_content=info_box_contents)
        fig.add_layer(makers_layer)

        # Plot shorted TSPTW route
        fig = self.add_multiple_directions_layer(fig, locations)
        if save is True:
            self.save_figure_to_html(fig)
        return fig

    def add_multiple_directions_layer(self, fig, locations):
        locations += [locations[0]]
        list_waypoints = [DirectionDescriptor(desc).get_waypoints() for desc in self.tsptw_data.descriptions]
        for i in range(len(locations) - 1):
            route_layer = gmaps.directions_layer(locations[i], locations[i + 1], waypoints=list_waypoints[i],
                                                 show_markers=False)
            # Avoid sending many requests
            fig.add_layer(route_layer)
        return fig

    def save_figure_to_html(self, fig, output_loc='./tsptw_vis.html'):
        # Cannot export DirectionLayerView
        embed_minimal_html(output_loc, views=[fig])

    def print_readable_description(self):
        for i, desc in enumerate(self.tsptw_data.descriptions):
            if i == 0:
                print('Depot')
            else:
                print(i)
            dir_des = DirectionDescriptor(desc)
            print(dir_des)
        print('Complete')


class DirectionDescriptor:
    def __init__(self, description):
        self.description = description[0]

    def __str__(self):
        self.start = self.description['legs'][0]['start_address']
        self.end = self.description['legs'][0]['end_address']
        message = 'START: {}\n'.format(self.start)
        for step in self.description['legs'][0]['steps']:
            message += '--- {}\n'.format(step['html_instructions'])
        message += 'END: {}\n'.format(self.end)
        soup = BeautifulSoup(message)
        text = soup.get_text()
        return text

    def get_waypoints(self, ):
        waypoints = []
        for step in self.description['legs'][0]['steps']:
            lat = step['end_location']['lat']
            lng = step['end_location']['lng']
            waypoints.append((lat, lng))
        return waypoints if len(waypoints) < 23 else waypoints[:23]


def generate_tw(json_data):
    et = np.array(json_data['ET_i']) * 60
    lt = np.array(json_data['LT_i']) * 60
    time_window = list(zip(et.tolist(), lt.tolist()))
    time_window = time_window[-1:] + time_window[1:-1]
    idx_ = json_data['Location']
    idx_ = np.array(idx_) + 1
    idx_ = [0] + idx_.tolist()
    return idx_, time_window


def print_problem_summary(num_stores, depart_time, finish_time):
    print('Total Store: ', num_stores)
    print('Total Warehouse: 1')
    print('Departure time: ', depart_time)
    print('Finished time: ', finish_time)


def convert_end2end(filename):
    gmaps.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    GG_CLIENT = googlemaps.Client(key=os.getenv('GOOGLE_API_KEY'))
    assert GG_CLIENT is not None, "Please check Google API KEY"
    store_locs = '../data/Location_BaDinh.xlsx'
    df = pd.read_excel(store_locs)
    warehouse = (21.078295, 105.966889)
    lats = [warehouse[0]] + list(df.correct_lat)
    lngs = [warehouse[1]] + list(df.correct_lng)
    locs = list(zip(lats, lngs))
    sample = json.load(open(filename, 'r'))
    stores, tws = generate_tw(sample)
    locations = [locs[i] for i in stores]
    # Save data into json
    json_data = {}
    json_data['destination'] = []
    depot = 0
    for latlng in locations:
        geocode_res = GG_CLIENT.reverse_geocode(latlng)
        json_data['destination'].append(geocode_res[0])
    json_data['time_window'] = tws
    json_data['depot'] = depot
    json_data['metadata'] = {}
    json_filename = filename[filename.rfind('/') + 1:-4]
    json.dump(json_data, open('./{}_tsptw.json'.format(json_filename), 'w'))
    # Load data from json
    json_data = json.load(open('./{}_tsptw.json'.format(json_filename), 'r'))
    print_problem_summary(len(stores) - 1, time.strftime("%d/%m/%y %H:%M:%S", time.localtime()), None)
    return json_filename


file_data = '../data/tw_data/data_9_1.txt'
json_filename = convert_end2end(file_data)
json_filename = os.path.join('..', 'notebook', json_filename + '_tsptw.json')
tsptw = TSPTW()
tsptw.read(json_filename)
tsptw.run()
vis = TSPTWVis(tsptw, rps=0.1)
vis.print_readable_description()
fig_widget = vis.draw_figure(save=True)


figure = plt.figure(figsize=(5, 5))
# ax = figure.add_subplot(111)


display(fig_widget)
plt.show()

print('Finish')