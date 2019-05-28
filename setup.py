# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os import listdir
from os.path import abspath, join, split, splitext, isdir

with open('README-PYPI.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

def recur_helper(li, root):
    root_dir = abspath(join(__file__, root))

    children = listdir(root_dir)

    tmp_li = []
    for c in children:
        name = f"{root}/{c}"
        if isdir(join(root_dir, c)):
            recur_helper(li, name)
        else:
            tmp_li.append(name.replace('../', ''))

    if tmp_li:
        li.append((root.replace('../', ''), tmp_li))

def get_data_files(directories):
    data_files = []

    for d in directories:
        recur_helper(data_files, d)

    return data_files

setup(
    name='parmapp',
    version='0.0.12',
    description='PARM App is an automated Pipeline, Alerting, Reporting and Monitoring tool',
    long_description=readme,
    author='Sid Telang',
    author_email='siddharth.j.telang@gmail.com',
    url='',
    license=license,
    packages=['ansible','output', 'templates', 'parm'],
    package_dir={'ansible': 'ansible', 'output': 'output', 'templates': 'templates'},
    package_data={'ansible': ['group_vars/*.yaml'], 'output': ['*.yml'], 'templates': ['ansible/*.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'parm = parm.main:main']},
    install_requires=[
          'boto3','pyyaml','requests','simplejson','jinja2','boto','ansible','subprocess.run','docopt','progressbar','sphinx','sphinx_rtd_theme','aiohttp','asyncio',
      ],
)
