import subprocess
import shutil
from threading import Thread
from queue import Queue
import numpy as np
from pathlib import Path

import imaging

from utils.logging import get_logger_for_module
from utils.resources import ResourceManager
from data_models import MontageData


LOG = get_logger_for_module(__name__)

class MontageProcessor():

    required_cpus = 1
    processors_by_session = {}

    @classmethod
    def for_session(cls, session):
        if not session in cls.processors_by_session:
            processor = cls(session)
            cls.processors_by_session[session] = processor
        return cls.processors_by_session[session]


    def __init__(self, session):
        self.session = session
        self.tracked = []
        self.queue = Queue()


    def sync_with_db(self):
        montages = MontageData.fetch_all(self.session.db)
        untracked = [m for m in montages if m.base_name not in self.tracked]
        self.tracked.extend([m.base_name for m in untracked])
        unprocessed = [m for m in untracked if m.preview is None]
        for m in unprocessed: self.queue.put(m)


    def run(self):
        self.sync_with_db()

        if self.queue.empty():
            return

        if ResourceManager.request_cpus(MontageProcessor.required_cpus):
            try:
                montage = self.queue.get()
                process_thread = Thread(
                    target=self.process_montage,
                    args=[montage]
                )
                process_thread.start()
            except Exception as e:
                ResourceManager.release_cpus(MontageProcessor.required_cpus)
                self.queue.put(montage)
                LOG.exception(e)


    def process_montage(self, montage):
        src = Path(montage.path)
        dst = Path(self.session.processing_directory) / montage.base_name
        binned = self.bin_montage_stack(src, montage.section, dst.with_suffix('.binned'))
        coords = self.extract_piece_coords_from_montage_stack(binned, dst.with_suffix('.coords'))
        blended = self.blend_montage_stack(binned, coords, dst.with_suffix('.blended'))
        preview = self.preview_montage(blended, dst.with_suffix('.preview.png'))
        montage.preview = str(preview)
        montage.push(self.session.db)


    # This function can return piece coordinates but I
    # kept them seperate to make things a little more clear
    def bin_montage_stack(self, src, section, dst):
        command = ' '.join([
            f'{get_config().imod_edmont_full_path}',
            f'-imin {src}',
            f'-imout {dst}',
            f'-secs {section}',
            '-bin 4',
            '> /dev/null'
        ])
        LOG.info(f'Binning montage pieces for {src} to {dst}')
        LOG.debug(f'Running command "{command}"')
        output = subprocess.run(command, shell=True, capture_output=True, check=True)
        return dst


    def extract_piece_coords_from_montage_stack(self, src, dst):
        command = ' '.join([
            f'{get_config().imod_extractpieces_full_path}',
            f'-input {src}',
            f'-output {dst}'
            '> /dev/null'
        ])
        LOG.info(f'Extracting piece coordinates from {src}')
        LOG.debug(f'Running command "{command}"')
        output = subprocess.run(command, shell=True, capture_output=True, check=True)
        return dst


    def blend_montage_stack(self, src, coords, dst):
        command = ' '.join([
            f'{get_config().imod_blendmont_full_path}',
            f'-imin {src}',
            f'-imout {dst}',
            f'-plin {coords}',
            f'-roo {dst}',
            '> /dev/null'
        ])
        LOG.info(f'Blending montage pieces for {src}')
        LOG.debug(f'Running command "{command}"')
        subprocess.run(command, shell=True, capture_output=True, check=True)
        return dst


    def preview_montage(self, src, dst):
        image_stack = imaging.load(str(src), format='mrc')
        image = image_stack[0]
        image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
        imaging.save(image, str(dst))
        return dst
