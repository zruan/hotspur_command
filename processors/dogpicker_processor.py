import os
import time
from glob import glob
from threading import Thread
import subprocess
import imaging
import numpy as np
import json

from data_models import AcquisitionData, MotionCorrectionData, CtfData, DogpickerData
from utils.resources import ResourceManager
from utils.config import get_config
from utils.logging import get_logger_for_module

LOG = get_logger_for_module(__name__)

def pretty_floats(obj):
    if isinstance(obj, float):
        return str(int(obj+0.5))
    elif isinstance(obj, np.float32):
        return str(int(obj+0.5))
    elif isinstance(obj, dict):
        return dict((k, pretty_floats(v)) for k, v in obj.items())
    elif isinstance(obj, (list, tuple)):
        return list(map(pretty_floats, obj))             
    return obj

def log(image, size):
    # this is the sigma that gives zero-crossings at given radius
    sigma = ( size / 2.0 ) / np.sqrt(2)
    # return scale-normalized result by multiplying with sigma^2
    return -imaging.filters.laplace(image, sigma)*sigma*sigma

def zoom_peaks(peaks, zoom):
    return [(tuple(np.array(p)*(1.0/np.array(zoom))), v, s) for p, v, s in peaks]

def peak_mean(peak, radius, image):
    lr = int(max(0,  peak[0][0] - radius))
    rr = int(min(image.shape[0], peak[0][0] + radius))
    lc = int(max(0,  peak[0][1] - radius))
    rc = int(min(image.shape[1], peak[0][1] + radius))
    stdv = np.std(image[lr:rr, lc:rc])
    return stdv

class DogpickerProcessor():

    required_cpus = 1
    processors_by_session = {}

    @classmethod
    def for_session(cls, session):
        try:
            return cls.processors_by_session[session]
        except:
            processor = cls(session)
            cls.processors_by_session[session] = processor
            return processor


    def __init__(self, session):
        self.session = session

        self.tracked = []
        self.queued = []
        self.finished = []

        self.sync_with_db()

    def sync_with_db(self):
        dogpicker_data_models = DogpickerData.fetch_all(self.session.db)
        base_names = [model.base_name for model in dogpicker_data_models]
        self.tracked = base_names.copy()
        self.finished = base_names.copy()

    def update_tracked_data(self):
        motioncor_data_model = MotionCorrectionData.fetch_all(self.session.db)
        for model in motioncor_data_model:
            if model.base_name not in self.tracked:
                self.tracked.append(model.base_name)
                self.queued.append(model)
        self.queued.sort(key=lambda model: model.time)

    def run(self):
        self.update_tracked_data()

        if len(self.queued) == 0:
            return

        if ResourceManager.request_cpus(DogpickerProcessor.required_cpus):
            try:
                motion_correction_data = self.queued.pop()
                acquisition_data = AcquisitionData(motion_correction_data.base_name)
                acquisition_data.fetch(self.session.db)
                process_thread = Thread(
                    target=self.process_data,
                    args=(acquisition_data, motion_correction_data)
                )
                process_thread.start()
            except:
                ResourceManager.release_cpus(DogpickerProcessor.required_cpus)

    

    def process_data(self, acquisition_data, motion_correction_data):
        if motion_correction_data.dose_weighted_image_file is not None:
            aligned_image_file = motion_correction_data.dose_weighted_image_file
        else:
            aligned_image_file = motion_correction_data.aligned_image_file
        output_file_base = os.path.join(self.session.processing_directory, acquisition_data.base_name)
        output_file = '{}_dogpicker.json'.format(output_file_base)


        try:
            image = imaging.load(aligned_image_file)[0]    
       
            mint = None
            maxt = None
            debug = None
            meanmax = None
            sizes = np.logspace(np.log10(30), np.log10(300) ,num=20)
            idogpicker_data = {}
            for size in sizes:
                keys = list(self.detect(image, size, mint, maxt, debug, meanmax))
            
                LOG.debug("%i -> %i" % (size, len(keys)))
                idogpicker_data[int(size+0.5)] = keys
            with open(output_file,'w') as fp:
                json.dump(pretty_floats(idogpicker_data),fp)
            data_model = DogpickerData(acquisition_data.base_name)
            data_model.time = time.time()
            data_model.dogpicker_file = output_file
        

       
            data_model.push(self.session.db)
        
        except Exception as e:
            LOG.error("Dogpicker failed")
            LOG.error(e)

            pass

        

        self.finished.append(acquisition_data.base_name)

        ResourceManager.release_cpus(self.required_cpus)



    def detect(self, image, size, mint=None, maxt=None, debug=None, meanmax=None):
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
            peaks = [(p, v, peak_mean((p, v), reduced_size/2, reduced_image)) for p, v in peaks]
            
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
            peaks = [(p, (1+v)*1000, (1+s)*1000) for p, v, s in peaks]
            return zoom_peaks(peaks, [rzoom, czoom])
        return []
    