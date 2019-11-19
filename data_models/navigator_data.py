from data_models import DataModel

class NavigatorData(DataModel):

    def __init__(self, base_name):
        super().__init__(base_name)

        self.path = None
        self.atlas = None
        self.squares = None
