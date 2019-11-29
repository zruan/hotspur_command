import subprocess
import shutil
import numpy as np
from pathlib import Path

import imaging

from hotspur_utils.logging_utils import get_logger_for_module
from data_models import MontageData


LOG = get_logger_for_module(__name__)

class MontageProcessor():

    processors_by_session = {}

    batch_size = 1

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
        self.queued = []


    def run(self):
        montages = MontageData.fetch_all(self.session.db)
        montages = [m for m in montages if m.preview is None]
        queued_names = [m.base_name for m in self.queued]
        montages = [m for m in montages if m.base_name not in queued_names]
        self.queued.extend(montages)
        stacks = [m.path for m in self.queued]
        stacks = list(set(stacks))
        stacks = [Path(p) for p in stacks]
        stacks = stacks[:MontageProcessor.batch_size]

        for s in stacks:
            try:
                previews = self.process_montage_stack(s)
                montages = [m for m in self.queued if m.path == str(s)]
                for m in montages: m.preview = str(previews[m.section])
                for m in montages: m.push(self.session.db)
                self.queued = [m for m in self.queued if m not in montages]
            except Exception as e:
                LOG.exception(e)
                continue


    def process_montage_stack(self, path):
        dst_base = Path(self.session.processing_directory) / path.stem
        binned = self.bin_montage_stack(path, dst_base.with_suffix('.binned'))
        coords = self.extract_piece_coords_from_montage_stack(binned, dst_base.with_suffix('.coords'))
        blended = self.blend_montage_stack(binned, dst_base.with_suffix('.blended'), coords)
        previews = self.preview_montage_stack(blended, dst_base.with_suffix(''), suffix='.preview.png')
        return previews


    # # def flatten_relative_path(self, path, parent):
    # #     relative_path = path.relative_to(parent)
    # #     return str(relative_path).replace('/', '-')


    def bin_montage_stack(self, src, dst):
        command = ' '.join([
            shutil.which('edmont'),
            f'-imin {src}',
            f'-imout {dst}',
            '-bin 2',
            '> /dev/null'
        ])
        LOG.info(f'Binning montage pieces for {src} to {dst}')
        LOG.debug(f'Running command "{command}"')
        output = subprocess.run(command, shell=True, capture_output=True, check=True)
        return dst


    def extract_piece_coords_from_montage_stack(self, src, dst):
        command = ' '.join([
            shutil.which('extractpieces'),
            f'-input {src}',
            f'-output {dst}'
            '> /dev/null'
        ])
        LOG.info(f'Extracting piece coordinates from {src}')
        LOG.debug(f'Running command "{command}"')
        output = subprocess.run(command, shell=True, capture_output=True, check=True)
        return dst


    def blend_montage_stack(self, src, dst, coords):
        command = ' '.join([
            shutil.which('blendmont'),
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


    def preview_montage_stack(self, src, dst_base, suffix):
        image = imaging.load(str(src), format='mrc')
        image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
        sections = np.split(image, image.shape[0])
        outputs = []
        for i, section in enumerate(sections):
            section = np.squeeze(section)
            dst = dst_base.with_suffix(f'.{i}{suffix}')
            imaging.save(section , str(dst))
            outputs.append(dst)
        return outputs
