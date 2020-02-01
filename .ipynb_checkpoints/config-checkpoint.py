import os
import yaml
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config_file = open('config.yml', 'r')
CONFIG = yaml.load(config_file, Loader=yaml.FullLoader)


class Program:
    SOLVER = 'lkh'
    SECRET_KEY = 'GOOGLE_API_KEY'
    METRIC = 'time'
    FORMAT = 'tsplib95'


def config_project_structure():
    # Default values
    default_structure = {'OUTPUT': 'output',
                         'SOLVER': 'solver',
                         'GENERATOR': 'generator',
                         'SAMPLE': 'sample',
                         'DATA': 'data',
                         'ENV': 'env'}
    default_keys = default_structure.keys()
    # Validate key-value of project structure
    structure = CONFIG.get('PROJECT_STRUCTURE', default_structure)
    for key in default_keys:
        if key not in structure:
            structure[key] = default_structure[key]
    # Generator projet structure
    for key in structure.keys():
        folder = structure[key]
        if not os.path.exists(folder):
            os.mkdir(folder)
            logger.debug('{} is make by default'.format(folder))
    # Finish


def config_main_program():
    global PROGRAM
    # Default values
    default_program = {'SOVLER': 'lkh',
                       'MAP_API': 'google',
                       'ENV_SECRET_KEY': 'GOOGLE_API_KEY',
                       'METRIC': 'time'}
    default_keys = default_program.keys()
    # Validate key-value of project structure
    program = CONFIG.get('PROJECT_STRUCTURE', default_program)
    for key in default_keys:
        if key not in program:
            program[key] = default_program[key]
    # Generate object for program
    PROGRAM.SOLVER = program['SOLVER']
    PROGRAM.SECRET_KEY = os.getenv(program['ENV_SECRET_KEY'])
    PROGRAM.METRIC = program['METRIC']
    PROGRAM.FORMAT = program['FORMAT']


PROGRAM = Program()
config_project_structure()
config_main_program()
