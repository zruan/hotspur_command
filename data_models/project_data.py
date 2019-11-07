from data_models import DataModel


class ProjectData(DataModel):

    def __init__(self, base_name=None):
        super().__init__(base_name)

        self.ignored_keys = ['db']

        self.db = None

        self.name = None
        self.hash = None
        
        self.sessions = None

