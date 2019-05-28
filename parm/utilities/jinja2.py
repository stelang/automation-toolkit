from . import write_file, get_conf_file
import jinja2, os, sys
from jinja2 import Environment 
"""
Generic Render template function
"""
def render_template(template, params):
    env = Environment()
    templatepath = get_conf_file('../../templates')
    filename = ''.join((
        templatepath,
        ("/" + template
    )))

    template = env.from_string(open(filename).read())
    return template.render(params)