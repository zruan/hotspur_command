from data_models import DataModel


class UserSessionData(DataModel):

    def __init__(self, base_name=None):
        super().__init__(base_name)

        self.dogpicker_state = None