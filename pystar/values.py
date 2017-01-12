

from pyparsing import *


Int = Word(nums) 
Float = Optional('-') + Word(nums) + Optional('.' + Word(nums)) + Optional('e' + Optional('+') + Optional('-' ) + Word(nums))
Int.setParseAction(lambda x: int( ''.join(x)))
Float.setParseAction(lambda x: float( ''.join(x)))
Number = ( Float | Int )
#Number = Regex(r'\d+(\.\d*)?([eE]\d+)?')

uqstr = Word(alphanums+"/_-.:@")
sqstr = Suppress("'") + CharsNotIn("'") + Suppress("'")
dqstr = Suppress('"') + CharsNotIn('"') + Suppress('"')
mqstr = Suppress(';') + CharsNotIn(';') + Suppress(';')
NumberedString = Int + '@' + uqstr
NumberedString.setParseAction(lambda x: (x[2],x[0]))

def striplines(lines):
    stripped = []
    for line in lines.split('\n'):
        stripped += [line.strip()]
    return '\n'.join(stripped)

mqstr.setParseAction(lambda x: map(striplines, x))

String = sqstr | dqstr | mqstr | uqstr
Comment = Suppress('#') + Suppress(restOfLine)
CodeName = CharsNotIn('\n\t\r ') + Optional(Comment)
DataName = Suppress('_') + CodeName + Optional(Comment)
Keyword = Suppress('data_') | Suppress('loop_') | Suppress('save_') | Suppress('stop_')
Value = (~Keyword) + (~DataName) + (  NumberedString | Number  | String ) + Optional(Comment)
Values = OneOrMore(Value)
DataItem = Group(DataName + Value)
DataItems = OneOrMore(Comment | DataItem)


def parse_data_item(parsed):
    return { parsed[0][0]: parsed[0][1] }


def parse_data_items(parsed):
    merged = {}
    for item in parsed:
        for key in item:
            merged[key] = item[key]
    return merged


DataItem.setParseAction(parse_data_item)
DataItems.setParseAction(parse_data_items)


def encode(data):
    raise NotImplemented()


def test():
    print(Values.parseString('''
300.000000 51768.988281 52917.800781    61.779999     2.700000    5.000000    -0.044560 Micrographs/15jul17b_00030gr_00002sq_v02_00003hl_v01_00011en.ctf:mrc 58824.000000     0.100000 Micrographs/15jul17b_00030gr_00002sq_v02_00003hl_v01_00011en.mrc
300.000000 50249.441406 51650.851562    45.150002     2.700000     5.000000     0.099240 Micrographs/15jul17b_00030gr_00002sq_v02_00003hl_v01_00012en.ctf:mrc 58824.000000     0.100000 Micrographs/15jul17b_00030gr_00002sq_v02_00003hl_v01_00012en.mrc
  '''))
    # print(DataItems.parseString('''
    #    _a 1 _b 2
    #    _c 3 # now
    #    test
    #    _d 6
    #    '''))


if __name__ == '__main__':
    test()
