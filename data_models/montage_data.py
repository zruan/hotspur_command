from data_models import DataModel

class MontageData(DataModel):

    def __init__(self, base_name):
        super().__init__(base_name)

        self.path = None
        self.section = None
        self.preview = None

        # (x, y) is the bottom left point
        self.x = None
        self.y = None
        self.width = None
        self.height = None
