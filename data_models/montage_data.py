from data_models import DataModel

class MontageData(DataModel):

    def __init__(self, base_name):
        super().__init__(base_name)

        self.path = None
        self.section = None

        self.preview = None

        self.corners = None
        self.position = None
        self.scaleMatrix = None
        self.dimensions = None