class Rect():

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.area = width * height

    def overlaps(self, other):
        return does_overlap(self, other)


def create_rect_by_corners(corner_points):
    corner_points.sort(key=lambda p: p[0] + p[1])
    bottom_left = corner_points[0]
    top_right = corner_points[3]
    width = top_right[0] - bottom_left[0]
    height = top_right[1] - bottom_left[0]
    # extents = map(operator.add, bottom_left, top_right)
    return create_rect_by_origin(*bottom_left, width, height)


def create_rect_by_origin(x, y, width, height):
    return Rect(x, y, width, height)


def does_overlap(rect1, rect2):
   return rect1.x < rect2.x + rect2.width
      and rect1.x + rect1.width > rect2.x
      and rect1.y < rect2.y + rect2.height
      and rect1.y + rect1.height > rect2.y
