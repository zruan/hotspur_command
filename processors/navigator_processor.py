from pathlib import Path
import time

from utils.logging import get_logger_for_module
from data_models import NavigatorData, MontageData


LOG = get_logger_for_module(__name__)

class NavigatorProcessor():

    processors_by_session = {}

    tracking_interval = 60

    @classmethod
    def for_session(cls, session):
        if not session in cls.processors_by_session:
            processor = cls(session)
            cls.processors_by_session[session] = processor
        return cls.processors_by_session[session]


    def __init__(self, session):
        self.session = session

        self.nav = None
        self.suffix = '.nav'
        self.time_since_last_tracking = None
        self.sync_with_db()


    def sync_with_db(self):
        data = NavigatorData.fetch_all(self.session.db)
        if len(data) > 0:
            self.current_nav = max(data, key=lambda d: d.time)
        LOG.debug(f"Fetched navigator data model for session {self.session.name}")


    def run(self):
        if self.time_since_last_tracking is None or time.time() - self.time_since_last_tracking >= NavigatorProcessor.tracking_interval:
            navs = self.find_navigators()
            self.time_since_last_tracking = time.time()
        else:
            return
        navs = self.find_navigators()
        if len(navs) == 0:
            LOG.debug('Did not find any nav files')
            return

        current_nav = self.get_most_recent_navigator(navs)
        if self.nav is not None and self.nav.time >= current_nav.time:
            LOG.debug(f'Current nav {self.nav.path} is already the newest nav')
            return

        try:
            current_nav, maps = self.process_navigator(current_nav)
            LOG.info("Pushing NAV")
            current_nav.push(self.session.db)
            maps = [m for m in maps if m._id not in self.session.db]
            for m in maps: m.push(self.session.db)
            self.nav = current_nav
        except Exception as e:
            LOG.exception(e)


    def find_navigators(self):
        paths = Path(self.session.directory).glob(f'*{self.suffix}')
        navs = [self.model_nav(p) for p in paths]
        return navs


    def model_nav(self, path):
        model = NavigatorData()
        model.path = str(path)
        model.time = path.stat().st_mtime
        return model


    def get_most_recent_navigator(self, navs):
        return max(navs, key=lambda n: n.time)


    def process_navigator(self, nav):
        items = self.parse_nav_items(nav)
        map_items = [i for i in items if self.is_map_item(i)]
        if len(map_items) == 0:
            LOG.info(f'Did not find any map items for nav {nav}')
            return nav, []

        saved_path = self.get_nav_saved_path(nav)
        convert_path_fn = self.get_convert_path_fn(saved_path, nav.path)
        for i in map_items: i['MapFile'] = convert_path_fn(i['MapFile'])
        map_items = [i for i in map_items if self.map_file_exists(i)]

        maps = [self.process_map_item(i) for i in map_items]
        
        atlases = [m for m in maps if self.is_atlas(m)]
        if len(atlases) > 0:
            current_atlas = atlases[-1]
            nav.atlas = current_atlas.base_name

        squares = [m for m in maps if self.is_square(m)]
        if len(squares) > 0:
            #squares = self.remove_overlaping_squares(squares)
            nav.squares = [s.base_name for s in squares]
        return nav, maps


    def get_nav_saved_path(self, nav):
        with open(nav.path) as fp:
            for line in fp.readlines():
                if line.startswith('LastSavedAs'):
                    saved_path_string = line.split(' = ')[1]
                    return Path(saved_path_string)


    def get_convert_path_fn(self, old_path, new_path):
        # SerialEM saves windows back with backslashes. Python cannot deal with backslashes
        old_path = str(old_path).replace('\\', '/')
        old_path = Path(old_path)
        new_path = Path(new_path)

        session_parent_index = 0
        for i, path in enumerate(new_path.parents):
            if path == self.session.directory:
                session_parent_index = i + 1

        old_path_start = str(old_path.parents[session_parent_index])

        def convert_path_fn(old_path):
            old_path_str = str(old_path)
            old_path_str = old_path_str.replace('\\', '/')
            new_path_str = old_path_str.replace(old_path_start, self.session.directory)
            return Path(new_path_str)

        return convert_path_fn


    def parse_nav_items(self, nav):
        items = []
        with open(nav.path) as fp:
            item_data = {}
            for line in fp.readlines():
                if line.startswith('[Item ='):
                    items.append(item_data)
                    item_data = {}
                elif ' = ' in line:
                    key, value = line.split(' = ')
                    key = key.strip()
                    value = value.strip().split()
                    if len(value) == 1: value = value[0]
                    item_data[key] = value
            items.append(item_data)
        return items


    def is_map_item(self, item):
        return 'Type' in item and item['Type'] == '2'


    def map_file_exists(self, map_item):
        return Path(map_item['MapFile']).exists()


    def process_map_item(self, map_item):
        map_path = Path(map_item['MapFile'])
        map_section = int(map_item['MapSection'])
        map_name = f'{map_path.stem}-{map_section}'
        model = MontageData(map_name)
        model.path = str(map_path)
        model.section = map_section

        position = map_item['RawStageXY']
        position = [float(n) for n in position]
        model.position = position

        net_viewshift = map_item['NetViewShiftXY']
        net_viewshift = [float(n) for n in net_viewshift]
        model.net_viewshift = net_viewshift

        dimensions = map_item['MapWidthHeight']
        dimensions = [float(n) for n in dimensions]
        model.dimensions = dimensions

        scale_matrix = map_item['MapScaleMat']
        scale_matrix = [float(n) for n in scale_matrix]
        model.scale_matrix = scale_matrix

        corners = zip(map_item['PtsX'], map_item['PtsY'])
        corners = [(float(x), float(y)) for x,y in corners]
        # Last corner is duplicate of the first corner
        corners = corners[:-1]
        model.corners = corners

        model.is_montage = int(map_item['MapMontage']) > 0

        return model


    def get_distance(self, p1, p2):
        x_distance = abs(p1[0] - p2[0])
        y_distance = abs(p1[1] - p2[1])
        distance = (x_distance ** 2 + y_distance ** 2) ** 0.5
        return distance

    # these are very low tech ways of testing box map size
    # assumes maps are polygons with four corner points (aka a box)
    # tests the length of one edge
    def is_atlas(self, map):
        distance = self.get_distance(map.corners[0], map.corners[1])
        return distance > 800


    def is_square(self, map):
        distance = self.get_distance(map.corners[0], map.corners[1])
        return distance < 400


    def remove_overlaping_squares(self, maps):
        new_maps = []
        # Reversed to prioritize most recent maps (at bottom of navigator file)
        maps.reverse()
        for m in maps:
            overlap = False
            for n in new_maps:
                distance = self.get_distance(m.position, n.position)
                if distance < 50:
                    overlap = True
                    break
            if not overlap:
                new_maps.append(m)
        return new_maps

