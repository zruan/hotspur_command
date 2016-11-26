'''
goal is to take a parsed STAR file that uses native Python structures, and convert loops to optimized
numpy arrays with field names
'''

import star
# import numpy as np


def load(path):
    parsed = star.load(path)
    for key in parsed:
        if key == 'data_':
            parsed[key] = as_field_array(parsed[key])


def as_field_array(data):
    return data


if __name__ == '__main__':
    load('relion_particles.star')
