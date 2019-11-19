from hotspur_utils.logging_utils import get_logger_for_module
from hotspur_utils.rect import Rect
from data_models import NavigatorData


LOG = get_logger_for_module(__name__)

class NavigatorProcessor():

    processors_by_session = {}

    @classmethod
    def for_session(cls, session):
        try:
            return cls.processors_by_session[session]
        except:
            processor = cls(session)
            cls.processors_by_session[session] = processor
            return processor


    def __init__(self, session):
        self.session = session

        self.queued = []
        self.current_nav = None
        self.suffix = '.mdoc'

        self.sync_with_db()


    def sync_with_db(self):
        data = NavigatorData.fetch_all(self.session.db)
        self.tracked = {self.current_nav.path: self.current_nav.time}
        LOG.debug(f"Fetched navigator data model for session {self.session.name}")


    def run(self):
        navs = self.find_navigators()
        nav = self.get_most_recent_navigator(navs)
        if nav.time > self.current_nav.time:
            try:
                nav = process_navigator(nav)
                nav.push(self.session.db)
                self.current_nav = nav
            except Exception as e:
                logger.exception(e)


    def find_navigators(self):
        paths = Path(self.session.directory).glob(f'**/*{self.suffix}')
        navs = [self.model_nav(p) for p in paths]
        return navs


    def model_nav(self, path):
        model = NavigatorData(path.stem)
        model.path = str(path)
        model.time = path.stat().st_mtime
        return model


    def get_most_recent_navigator(self, navs):
        return max(navs, key=lambda n: n.time)


    def process_navigator(self, nav):
        items = self.parse_nav_items(nav)
        items = [i for i in items if self.is_map_item(i)]

        saved_path = self.get_nav_saved_path(nav)
        convert_path_fn = self.get_convert_path_fn(saved_path, nav.path)
        for i in items: i['MapFile'] = convert_path_fn(i['MapFile'])

        maps = [self.process_map_item(i) for i in items]
        maps = [m for m in maps if self.map_file_exists(m)]
        atlases = [m for m in maps if self.is_atlas(m)]
        nav.atlas = atlas[-1]
        squares = [m in maps if self.is_square(m)]
        nav.squares = self.remove_overlaping_squares(squares)


    def get_nav_saved_path(self, nav):
        with open(nav.path) as fp:
            for line in fp.readlines():
                if line.startswith('LastSavedAs'):
                    saved_path_string = line.split(' = ')[1]
                    return Path(saved_path_string)


    def get_convert_path_fn(self, old_path, new_path):
        i = 1
        while new_path.parts[-i] == old_path.parts[-i]:
            i += 1

        match_count = i - 1
        diff_parent_index = match_count - 1
        if num_matching_end_parts == 0:
            old_path_start = old_path
            new_path_start = new_path
        else
            old_path_start = old_path.parents[diff_parent_index]
            new_path_start = new_path.parents[diff_parent_index]

        def convert_path_fn(old_path):
            old_path_str = str(old_path)
            new_path_str = old_path_str.replace(old_path_start, new_path_start)
            return Path(new_path_str)

        return convert_path_fn


    def parse_nav_items(self, nav):
        items = []
        with open(nav.path) as fp:
            item_data = {}
            for line in fp.readlines():
                if line.startswith('[Item ='):
                    nav_items.append(item_data)
                    item_data = {}
                else:
                    key, value = line.split(' = ')
                    item_data[key.strip()] = value.strip().split()
        return items


    def is_map_item(self, item):
        return i['Type'] is not None and i['Type'] == '2'


    def process_map_item(self, map_item):
        return {
            'path': map_item['MapFile'],
            'corners': zip(map_item['PtsX'], map_item['PtsY']),
            'section': map_item['MapSection']
        }


    def map_file_exists(self, map):
        return Path(map['path']).exists()


    def is_atlas(self, maps):
        rect = create_rect_by_corners(map['corners'])
        return rect.width > 800 and rect.height > 800:


    def is_square(self, map):
        rect = create_rect_by_corners(map['corners'])
        return rect.width < 400 and rect.height < 400:


    def remove_overlaping_squares(self, maps):
        rects = {m: create_rect_by_corners(m['corners']) for m in maps}
        new_maps = []
        # Reverse to prioritize most recent maps
        for m in maps.reversed():
            for n in new_maps:
                if rects[m].overlaps(rects[n]):
                    overlap = True
                    break
            if not overlap:
                new_maps.append(m)
        return new_maps

