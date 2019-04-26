from data_models import DataModel


class SessionData(DataModel):

	def __init__(self):
		super().__init__('')

		self.session_id = None
		self.grid_id = None
		self.proposal_id = None
