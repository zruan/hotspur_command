from data_models import DataModel


class SessionData(DataModel):

    def __init__(self, base_name=None):
        super().__init__(base_name)

        self.ignored_keys = ['db', 'time']

        self.db = None

        self.name = None
        self.hash = None
        
        self.end_time = None

        self.sample_name = None
        self.project_name = None
        self.project_hash = None

        self.frames_directory = None
        self.processing_directory = None
