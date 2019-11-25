from data_models import DataModel


class SessionData(DataModel):

    def __init__(self, base_name=None):
        super().__init__(base_name)

        self.ignored_keys = ['db']

        self.db = None

        self.name = None
        self.long_name = None
        self.hash = None
        
        self.end_time = None

        self.sample= None
        self.project= None

        self.directory = None
        self.processing_directory = None
