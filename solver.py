from __future__ import print_function
import tsplib95
import os
import subprocess
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import util
import config as cfg
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Problem:
    def __init__(self, prob_type, metadata):
        self.prob_type = prob_type
        self.metadata = metadata


class Solver:
    def __init__(self, solver=cfg.PROGRAM.SOLVER):
        if solver == 'ORTool':
            self.__class__ = ORTool
        else:
            self.__class__ = LKH


class ORTool:
    def __init__(self, settings=None):
        self.settings = settings

    def solve(self, problem):
        if problem.prob_type == 'tsp':
            return self.find_tsp_solution(problem.metadata)

    @staticmethod
    def find_tsp_solution(metadata):
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]

        def output_solution(f_manager, f_routing, f_assignment):
            index = f_routing.Start(0)
            f_route = []
            while not f_routing.IsEnd(index):
                f_route += [f_manager.IndexToNode(index)]
                index = f_assignment.Value(f_routing.NextVar(index))
            return f_route

        distance_matrix = metadata['distance_matrix']
        depot = metadata.get('depot', 0)
        num_vehicles = metadata.get('num_vehicles', 1)
        manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicles, depot)
        routing = pywrapcp.RoutingModel(manager)
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
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
        id_filename = self.write_tsplib95_format(
                        duration_matrix=metadata['duration_matrix'],
                        time_window=metadata['time_window'],
                        depot=metadata['depot'])
        par_filename = self.write_par_file(id_filename)
        return self.execute_cmd(par_filename, id_filename)

    @staticmethod
    def execute_cmd(par_filename, id_filename):
        result = subprocess.run(['./solver/LKH-3.0.6/LKH', '{}'.format(par_filename)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # for l in result.stdout.decode("utf-8") .split('\n'):
        #     print(l)
        # for l in result.stderr.decode("utf-8") .split('\n'):
        #     print(l)
        if os.path.exists('./format/{}.sol'.format(id_filename)):
            sol = tsplib95.load_solution('./format/{}.sol'.format(id_filename))
            return sol.tours[0]
        return None

    @staticmethod
    def write_par_file(id_filename):
        filename = './format/{}.par'.format(id_filename)
        file = open(filename, 'w')
        file.write('PROBLEM_FILE = {}\n'.format('./format/{}.tsptw'.format(id_filename)))
        file.write('TOUR_FILE = {}\n'.format('./format/{}.sol'.format(id_filename)))
        file.close()
        return filename

    @staticmethod
    def write_tsplib95_format(**kwargs):
        id_filename = util.get_random_filename()
        filename = './format/{}.tsptw'.format(id_filename)
        file = open(filename, 'w')
        file.write('NAME : {}\n'.format('{}.tsptw'.format(id_filename)))
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
        return id_filename
