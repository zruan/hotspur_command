#!/usr/bin/env cky-python

import re
import sys
from collections import defaultdict as ddict
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
from matplotlib import pyplot as plt
import pystar2

def load(paths):
    """Loads resolution information from star files"""
    resolutions = ddict(dict)
    for file in paths:
        print(file)
        _it = re.search('run.+it(\d+)_model.star$', file)
        iteration = int(_it.group(1))
        print(iteration)
        data = pystar2.load(file)
        models = [(a.split('_')[-1],a) for a in data.keys() if "model_class_" in a]
        for (i, key) in models:
            res = 1000
            i = int(i)
            for row in list(data[key].values())[0]:
                if row[3] < 1:
                    resolutions[iteration][i] = res
                    print(i)
                    print(res)
                    break
                res = row[2]
    return resolutions

def bhattacharyya_distance(pd1, pd2):
    return np.sqrt(1.0 - np.sum(np.sqrt(pd1*pd2)))


iters = load(sys.argv[1:])
for it in sorted(iters):
    classes = iters[it]
    pts = [ '% 6.4f' % (classes[cl]) for cl in sorted(classes) ]
    print('% 4d' % (it), ' '.join(pts))

ys = []
xs = []
for it in sorted(iters):
    ys += [it]
    xs += [ [ iters[it][cl] for cl in sorted(iters[it]) ] ]
lines = plt.plot(ys, xs)

for clnm, pct in enumerate(xs[-1]):
    plt.text(ys[-1], pct, clnm+1, color=lines[clnm].get_color())

plt.savefig("Class_res.png")


   

