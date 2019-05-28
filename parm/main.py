"""
Parm.

Usage:
    parm create-dashboards <file>
    parm cleanup <file>
    parm host <file>
    parm monitors <file>
    parm pipeline <file>
    parm test <file>
    parm init
    parm -h | --help
    parm --version

Options:
    -h --help         Show this screen.
    --version         Show version.

Examples:
    parm create-dashboards parm.yaml

"""
from inspect import getmembers, isclass
from docopt import docopt
import logging

def main():
    """Parm app main"""
    import parm.commands
    logging.basicConfig(filename='fargate.log', level=logging.INFO)
    options = docopt(__doc__, version='0.0.10')
    for (k,v) in options.items():
        k = k.replace('-', '')
        if hasattr(parm.commands, k) and v:
            module = getattr(parm.commands, k)
            parm.commands = get_members(module)
            command = [command[1] for command in parm.commands if command[0] != 'Base'][0]
            command = command(options)
            command.run()

def get_members(module):
    commands = getmembers(module, isclass)
    
    _filter = lambda c: True if 'commands' in c[1].__module__ else False

    return list(filter(_filter, commands))

if __name__ == '__main__':
    main()
