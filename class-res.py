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
        data = pystar2.load(file)
        models = [(a.split('_'[-1],a))]
        for _cl,_it, _rem in re.findall('(\d+)\@.+it(\d+)_classes\.mrcs\s+(.+)\n', data):
            _pt = _rem.split()[0]
            classes[int(_it)][int(_cl)] = float(_pt)
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

plt.savefig("Class_occ.png")


   

