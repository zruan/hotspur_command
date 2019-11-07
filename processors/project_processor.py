from hotspur_utils.logging_utils import get_logger_for_module
from hotspur_utils.hash_utils import get_hash
from hotspur_utils.couchdb_utils import fetch_db

from data_models import ProjectData


logger = get_logger_for_module(__name__)

class ProjectProcessor():

    def __init__(self):
        self.projects = {}


    def update_project(self, session):
        name = session.project_name
        if name in self.projects:
            project = self.projects[name]
        else:
            logger.debug(f'Tracking project {name}')
            project = self.model_project(name)
            self.projects[name] = project

        if session.name not in project.sessions:
            project.sessions[session.name] = session.hash
            project.push(project.db)


    def model_project(self, name):
        project = ProjectData()
        project.name = name
        project.hash = get_hash(name)
        project.sessions = {}
        project.db = fetch_db(project.hash)
        project.fetch(project.db)
        return project







        # try:
        #     project_db = fetch_db(session.project_hash)
        #     doc = fetch_doc('project_data', project_db, True)
        #     if not 'sessions' in doc:
        #         doc['name'] = session.project_name
        #         doc['hash'] = session.project_hash
        #         doc['sessions'] = {session.name: session.hash}
        #         push_doc(doc, project_db)
        #         print(f'Create project data doc for project {session.project_name}')
        #         print(f'Added session {session.name} to session list')
        #     elif session.name in doc['sessions']:
        #         print('Session {} is already in session list for project {}'.format(
        #             session.name, session.project_name))
        #     else:
        #         doc['sessions'][session.name] = session.hash
        #         push_doc(doc, project_db)
        #         print('Added session {} to session list for project {}'.format(
        #             session.name, session.project_name))

        # except Exception as e:
        #     print('Failed to add session {} to session list for project {}'.format(
        #         session.name, session.project_name))
        #     print(e)
        #     raise e