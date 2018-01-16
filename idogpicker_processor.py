#from collection_processor import CollectionProcessor
import imaging
import numpy as np
import pyfs
from collection_processor_base import CollectionProcessor
import string

def log(image, size):
    # this is the sigma that gives zero-crossings at given radius
    sigma = ( size / 2.0 ) / np.sqrt(2)
    # return scale-normalized result by multiplying with sigma^2
    return -imaging.filters.laplace(image, sigma)*sigma*sigma


def detect(image, size, mint=None, maxt=None, debug=None, meanmax=None):
    zoom = min(1.0, 30.0 / size)
    reduced_image = imaging.filters.zoom(image, zoom)
    rzoom = float(reduced_image.shape[0]) / float(image.shape[0])
    czoom = float(reduced_image.shape[1]) / float(image.shape[1])
    reduced_size = np.mean([rzoom, czoom]) * size
    log_image = -log(reduced_image, reduced_size)
    peaks = list(imaging.detection.peaks.maxima(log_image, 3))
    if len(peaks):
        pvalues = np.sort(np.array([v for _, v in peaks]))
        if maxt is None:
            maxt = pvalues[-1]
        if mint is None:
            mint = pvalues[0]
        peaks = [(p, v) for p, v in peaks if v <= maxt]
        peaks = [(p, v) for p, v in peaks if v >= mint]
        if meanmax is not None:
            stdvs = [peak_mean(peak, reduced_size/2, reduced_image) for peak in peaks]
            peaks = [peak for peak, stdv in zip(peaks, stdvs) if stdv < meanmax]
            if debug:
                print('current peak stdv distribution:')
                counts, bins = np.histogram(stdvs, bins=10)
                for idx in range(len(counts)):
                    print('  % 13.2f -> % 13.2f: %d' % (bins[idx], bins[idx+1], counts[idx]))
        if debug: 
            print('current peak range: %f -> %f' % (mint, maxt))
            print('distribution within range:')
            print('  low threshold -> max threshold: peak count')
            counts, bins = np.histogram(pvalues, bins=10, range=(mint, maxt))
            for idx in range(len(counts)):
                print('  % 13.2f -> % 13.2f: %d' % (bins[idx], bins[idx+1], counts[idx]))
            save_peaks(reduced_image, log_image, peaks, reduced_size, debug)
        return zoom_peaks(peaks, [rzoom, czoom])
    return []


def peak_mean(peak, radius, image):
    lr = int(max(0,  peak[0][0] - radius))
    rr = int(min(image.shape[0], peak[0][0] + radius))
    lc = int(max(0,  peak[0][1] - radius))
    rc = int(min(image.shape[1], peak[0][1] + radius))
    stdv = np.std(image[lr:rr, lc:rc])
    return stdv

def zoom_peaks(peaks, zoom):
    return [(tuple(np.array(p)*(1.0/np.array(zoom))), v) for p, v in peaks]

def save_star(keypoints, path):
    with open(path, 'w') as dst:
        dst.write('''
data_

loop_
_rlnCoordinateX #1
_rlnCoordinateY #2
_rlnAnglePsi #3
_rlnClassNumber #4
_rlnAutopickFigureOfMerit #5
''')
        for keypoint in keypoints:
            psi = 0.0
            cls = 1
            dst.write('%.6f %.6f %.6f %d %.6f\n' % (keypoint[0][1], keypoint[0][0], psi, cls, keypoint[1]))


class IdogpickerProcessor(CollectionProcessor):

    def __init__(self,
                 process_id,
                 config,
                 filename,
                 suffix="",
                 size_range=[10,900],
                 size_steps=10,
                 **kwargs):
        CollectionProcessor.__init__(self, process_id, config, **kwargs)
        self.suffix = suffix
        self.size_range = size_range
        self.size_steps = size_steps
        self.filename = filename


    def process(self, mic):
        try:
            image = imaging.load(mic)[0]    
        except Exception as e:
            print('[error] failed to process image: %s, %s' % (mic, e))
            return
        mint = None
        maxt = None
        debug = None
        meanmax=None
        sizes = [self.size_range[0] + i * ((self.size_range[1] - self.size_range[0])/(self.size_steps-1)) for i in np.arange(self.size_steps)]
        for size in sizes:
            keys = list(detect(image, size, mint, maxt, debug, meanmax))
            star = pyfs.rext(mic, full=False) + '_%s.star' % (size)
            if len(keys) > 5:
                save_star(keys, star)
                print('found %d particles in image %s -> %s' % (len(keys), mic, star))


    def run_loop(self, config, replace_dict):
        self.process(
            string.Template(self.filename).substitute(replace_dict))
