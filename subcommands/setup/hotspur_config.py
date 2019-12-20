from pathlib import Path

from templates.loader import load_hotspur_template


def run(args):
    template, name = load_hotspur_template()
    destination = Path() / name
    with open(destination, 'w') as fp:
        fp.write(template)
    print(f'Saved {destination.resolve()}')

    print('')
    print('You should edit the hotspur config file before you move on')
    print('')