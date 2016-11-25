#!/eppec/storage/sw/cky-tools/site/bin/python

import argparse
import imaging
import pystar
import pyfs

import numpy as np


def arguments():

    def floatlist(string):
        return list(map(float, string.split(',')))

    parser = argparse.ArgumentParser(
        description='Converts an MRC image to a normalized png')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--mrc', nargs='+', help='path to MRC input image')
    group.add_argument('--star', help='path to STAR file with MRC images')
    group.add_argument('--glob', help='glob pattern for MRC images')
    
    parser.add_argument('-p', '--parallel', type=int, default=1,
                        help='number of images to process in parallel')
    parser.add_argument('-i', '--invert', default=False, action='store_true',
                        help='invert image so that particles are black on a white background')
    return parser.parse_args()


def dog_size(s1, s2):
    k = s2 / s1
    k2 = k**2
    k21 = k2 - 1
    return s1 / np.sqrt(k21 / (2 * k2 * np.log(k)))


def dog_ends(size, k):
    radius = float(size) / 2.0
    sigma = radius / np.sqrt( (2*k*k*np.log(k)) / (k*k-1) )
    return sigma, sigma * k


def sig_diff(s1, s2):
    return np.sqrt(s2*s2 - s1*s1)


def dog(image, size, k):
    s1, s2 = dog_ends(size, k)
    g1 = imaging.filters.gaussian(image, s1)
    g2 = imaging.filters.gaussian(image, s2)
    return ( g1 - g2 ) * ( float(size) / 2.0 ) * ( k - 1.0 )


def log(image, size):
    # this is the sigma that gives zero-crossings at given radius
    sigma = ( size / 2.0 ) / np.sqrt(2)
    # return scale-normalized result by multiplying with sigma^2
    return -imaging.filters.laplace(image, sigma)*sigma*sigma


def detect(image, size, mint=None, maxt=None, debug=None, meanmax=None):
    zoom = min(1.0, 15.0 / size)
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
            mint = max(0, pvalues[0])
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


def inrange(v, mint=None, maxt=None):
    if mint is None:
        mint = v
    if maxt is None:
        maxt = v
    return mint <= v <= maxt


def colorize_log_map(logimage, mint, maxt):
    colorized = imaging.filters.norm(logimage, 0.01, 0.01, -1.0, 1.0)
    colorized = imaging.filters.asRGB(logimage)
    lt = 1.0 - imaging.filters.scale(np.fmax(mint-logimage, -0.1), 0.0, 1.0)
    gt = 1.0 - imaging.filters.scale(np.fmax(logimage-maxt, -0.1), 0.0, 1.0)
    colorized[:, :, 0] *= gt
    colorized[:, :, 1] *= gt * lt
    colorized[:, :, 2] *= lt
    return colorized


def save_peaks(image, path):
    image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
    picks_path = path + '.preview.png'
    print(' saving png:', picks_path)
    imaging.save(image, picks_path)


def zoom_peaks(peaks, zoom):
    return [(tuple(np.array(p)*(1.0/np.array(zoom))), v) for p, v in peaks]


def log_peaks_as_keypoints(peaks, size):
    Keypoint = imaging.detection.keypoints.Keypoint
    return [Keypoint(p[0][0], p[0][1], size, 0.0, p[1], 1, 1) for p in peaks]


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


def load_micrographs_star(path):
    values = pystar.load(path)[0]['data_']
    fields = list(values)[0]
    index = fields.index('rlnMicrographName')
    return [x[index] for x in list(values.values())[0]]


def get_micrographs(args):
    if args.mrc:
        return args.mrc
    elif args.glob:
        import glob
        return glob.glob(args.glob)
    elif args.star:
        return load_micrographs_star(args.star)
    raise ValueError()


def argidx(arg, idx, default):
    try:
        return arg[idx]
    except IndexError:
        return default


if __name__ == '__main__':

    args = arguments()
    print(args)
    mics = get_micrographs(args)

    def process(mic):
        try:
            if args.star:
                mic = pyfs.join(pyfs.dpath(args.star), mic)
            image = imaging.load(mic)[0]    
        except KeyboardInterrupt:
            exit(-1)
        except Exception as e:
            print('[error] failed to process image: %s, %s' % (mic, e))
            return
        if args.invert:
            image = imaging.filters.invert(image)
        #mint = argidx(args.thresholds, 0, None)
        #maxt = argidx(args.thresholds, 1, None)
        #debug = None
        #if args.debug:
        debug = pyfs.rext(mic, full=False) + '_%s' % ("prev")
        #keys = list(detect(image, size, mint, maxt, debug, meanmax))
        #star = pyfs.rext(mic, full=False) + '_%s.star' % (args.label)
        #if len(keys) > 5:
        #    save_star(keys, star)
        #    print('found %d particles in image %s -> %s' % (len(keys), mic, star))
        save_peaks(image, debug)

    import multiprocessing as mp
    pool = mp.Pool(args.parallel)
    pool.map(process, mics)


