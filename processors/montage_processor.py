import imaging
from hotspur_utils.logging_utils import get_logger_for_module
from data_models import MontageData
from hotspur_utils.rect import create_rect_by_corners


LOG = get_logger_for_module(__name__)

class FramesFileProcessor():

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
        self.nav = self.get_most_recent_nav()
        self.montage_summaries = None


    def run(self):
        nav = self.get_most_recent_nav()
        if self.nav is not None and nav.time <= self.nav.time:
            LOG.debug(f'Nav {nav.path} is already up to date')
            return
        else:
            self.nav = nav

        self.montage_summaries = [*self.nav.squares, self.nav.atlas]
        path_strings = [m['path'] for m in montage_summaries]
        path_strings = list(set(path_strings))
        paths = [Path(p) for p in path_strings]
        for p in paths:
            try:
                self.process_montage(p)
            except Exception as e:
                LOG.exception(e)
                continue

        montages = [*self.process_montage(m) for m in montage_summaries]


    def get_most_recent_nav(self):
        return NavigatorData.fetch_all(self.session.db)[0]


    def process_montage(self, path):
        flat_name = self.flatten_relative_path(path, self.session.directory)
        dst_base = self.session.processing_directory / flat_name
        binned = self.bin_montage(path, dst_base.with_suffix('.binned'))
        coords = self.extract_piece_coords(path, dst_base.with_suffix('.coords'))
        blended = self.blend_montage(path, dst_base.with_suffix('.blended'), coords)
        previews = self.preview_montage(path, dst_base.with_suffix(''), suffix='.preview.png')
        for i, p in enumerate(previews):
            summaries = [s for s in self.montage_summaries if s['path'] == str(path)]
            summaries.sort(key=lambda s: s['section'])
            summary = summaries[i]
            summary['name'] = f'{flat_name}-{i}'
            summary['preview'] = p
            model = self.model_montage(summary)
            model.push(self.session.db)


    def flatten_relative_path(self, path, parent):
        relative_path = path.relative_to(parent)
        return str(relative_path).replace('/', '-')


    def bin_montage(self, src, dst):
        command = ' '.join([
            shutil.which('edmont'),
            f'-imin {src}',
            f'-imout {dst}',
            f'-bin {binning}',
            '> /dev/null'
        ])
        LOG.info(f'Binning montage pieces for {src} to {dst}')
        LOG.debug(f'Running command "{command}"')
        output = subprocess.run(command, shell=True, capture_output=True, check=True)
        return dst


    def extract_piece_coords(self, src, dst):
        command = ' '.join([
            shutil.which('extractpieces'),
            f'-input {src}',
            f'-output {dst)}'
            '> /dev/null'
        ])
        LOG.info(f'Extracting piece coordinates from {src}')
        LOG.debug(f'Running command "{command}"')
        output = subprocess.run(command, shell=True, capture_output=True, check=True)
        return dst


    def blend_montage(self, src, dst, coords):
        command = ' '.join([
            shutil.which('blendmont'),
            f'-imin {src}',
            f'-imout {dst}',
            f'-plin {coords}',
            f'-roo {dst}',
            '> /dev/null'
        ])
        LOG.info(f'Blending montage pieces for {montage.file}')
        LOG.debug(f'Running command "{command}"')
        subprocess.run(command, shell=True, capture_output=True, check=True)
        return out_path


    def create_preview(self, src, dst_base, suffix):
        image = imaging.load(src)[0]
        image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
        outputs = []
        for i, section in enumerate(image):
            dst = dst_base.with_suffix(f'_{i}{suffix}')
            imaging.save(image, dst)
            outputs.append(dst)
        return outputs


    def model_montage(self, summary):
        model = MontageData(path.stem)
        model.name = summary['name']
        model.path = summary['path']
        model.section = summary['section']
        model.time = Path(model.path).stat().st_mtime
        model.preview = summary['preview']
        rect = create_rect_by_corners(summary['corners'])
        model.__dict__.update(rect.__dict__)
        return model
