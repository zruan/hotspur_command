from data_models import DataModel


class SessionData(DataModel):

	def __init__(self, base_name=None):
		super().__init__(base_name)

		self.name = None
		self.db_name = None

		self.session = None
		self.grid = None
		self.user = None

		self.frames_directory = None
		self.processing_directory = None
