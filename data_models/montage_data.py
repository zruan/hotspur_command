from data_models import DataModel

class MontageData(DataModel):

    def __init__(self, base_name):
        super().__init__(base_name)

        self.path = None
        self.section = None

        self.preview = None

        self.corners = None
        self.position = None
        self.net_viewshift = None
        self.scale_matrix = None
        self.dimensions = None
        self.is_montage = None