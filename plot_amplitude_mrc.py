#!/eppec/storage/sw/cky-tools/site/bin/python
import imaging
import argparse
import pyfs
import numpy as np
import matplotlib.pyplot as plt


def arguments():

    def floatlist(string):
        return list(map(float, string.split(',')))

    parser = argparse.ArgumentParser(
        description='Converts an MRC image to a normalized png')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--mrc', nargs='+', help='path to MRC input image')
    
    return parser.parse_args()


if __name__ == '__main__':

    args = arguments()
    print(args)
    data = imaging.load(args.mrc[0])
    spectrum = np.zeros(data[0].shape[1]-1)
    counts = np.zeros(data[0].shape[1]-1)

    for index, v in np.ndenumerate(data[0]):
        if index[0] < 150:
            j = index[0] + 1
        else:
            j = 300 - index[0]
        k = index[1] + 1

        spec_index = int(np.round(np.sqrt(j*j + k*k)))
        if spec_index < 150:
            counts[spec_index-1] += 1
            spectrum[spec_index-1] += v

    for spec_index, v in enumerate(spectrum):
        if counts[spec_index] > 0:
            spectrum[spec_index] /= counts[spec_index]

    plt.plot(spectrum)
    plt.show()
