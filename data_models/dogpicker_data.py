from data_models import DataModel

class DogpickerData(DataModel):

    def __init__(self, base_name):
        super().__init__(base_name)

        self.dogpicker_file = None
        

