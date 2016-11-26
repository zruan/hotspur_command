'''
STAR Loops get returned as a Python dictionary with a key that is a tuple of the column names
  and a list with tuples of the values:

{(field1, field2, ...): [(value1, value2, ...), ...]}
'''

from pyparsing import *

from values import Value, Comment, DataName

Start = Suppress('loop_')

Fields = Group(OneOrMore(DataName | Comment))
Values = Group(OneOrMore(Value | Comment))
Loop = Start + Fields + Values


def parse_loop(munged):
    fields = tuple(munged[0])
    values = munged[1]
    c, n = len(fields), len(values)
    return { fields: [tuple(values[x:x+c]) for x in range(0, n, c)] }

Loop.setParseAction(parse_loop)


def test():
    print OneOrMore(Loop).parseString('''
        loop_
        _a
        _b #3
        # boo
        _c
        1 2 3 # test
        4 5 6
        loop_
        _a
        _b
        1 2
        3 4
        5 6
        ''')


if __name__ == '__main__':
    test()
