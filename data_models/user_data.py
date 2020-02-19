from data_models import DataModel

class UserData(DataModel):

    def __init__(self, base_name):
        super().__init__(base_name)

        self.excluded = False
