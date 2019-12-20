from pathlib import Path

from templates.loader import load_conda_template


def run(args):
    template, name = load_conda_template()
    destination = Path() / name
    with open(destination, 'w') as fp:
        fp.write(template)
    print(f'Saved {destination.resolve()}')

    print('')
    print('Create the conda environment using a command such as:')
    print(f'conda env create -f {name} -p /desired/env/path')
    print('')