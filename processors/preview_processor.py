import imaging
import pyfs
import string
from processors import CollectionProcessor

class PreviewProcessor(CollectionProcessor):

    def __init__(self,
                 process_id,
                 config,
                 filename,
                 suffix="",
                 zoom=0.25,
                 **kwargs):
        CollectionProcessor.__init__(self, process_id, config, **kwargs)
        self.suffix = suffix
        self.zoom = zoom
        self.filename = filename

    def create_preview(self, filename):
        image_data = imaging.load(filename)
        for i, image in enumerate(image_data):
            if len(image_data) == 1:
                num = ""
            else:
                num = str(i)
            image = imaging.filters.norm(image, 0.01, 0.01, 0, 255)
            image = imaging.filters.zoom(image, self.zoom)
            picks_path = pyfs.rext(filename) + self.suffix + num + '.preview.png'
            imaging.save(image, picks_path)

    def run_loop(self, config, replace_dict):
        self.create_preview(
            string.Template(self.filename).substitute(replace_dict))
