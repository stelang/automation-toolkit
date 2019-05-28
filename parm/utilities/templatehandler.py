from jinja2 import Environment, FileSystemLoader, PrefixLoader, meta, TemplateNotFound
from os import listdir
from os.path import isfile, join
from .directory import get_conf_file
import uuid

"""
TemplateHandler Class

Handles all jinja2 templates for program.
"""
class TemplateHandler:
    
    """
    Takes in file, or files, 
    and assigns to jinja2 environment.
    """
    def __init__(self, parm):
        self.parm = parm
        
        root = get_conf_file('../../templates')

        print(root)
        self.environment = Environment(loader=self.create_loader(root))
    
    """
    Takes in template_name, and a dictionary containing all fields
    that need to substituted in the template.
    
    Returns a the rendered template
    """
    def render_template(self, template_name, template_dict):
        
        template = self.environment.get_template(template_name)
        
        return template.render(**template_dict)
    

    """
    Gets all variables that need to substituted within the given template.
    
    Returns them as a set.
    """
    def get_template_vars(self, template_name):
        template_source = self.environment.loader.get_source(self.environment, template_name)[0]
        parsed_content = self.environment.parse(template_source)
        
        return meta.find_undeclared_variables(parsed_content)
    
    
    def get_rendered_templates(self, obj_type):
        templates = self.environment.list_templates(filter_func = lambda x: True if obj_type in x else False)
        
        rendered = []
        for temp in templates:
            vars = self.get_template_vars(temp)
            
            temp_dict = dict()
            
            self.parm_search(self.parm.__dict__, vars, temp_dict)

            for var in vars:
                if 'uuid' in var:
                    temp_dict[var] = uuid.uuid4()
                elif var == 'key' or var == 'value':
                    temp_dict[var] = '{{' + var + '}}'
                else:
                    print("%s - template value missing" % var)
            
            rendered.append(self.render_template(temp, temp_dict))
            
        return rendered
    """
    Recursive method to search parm for template values.

    """
    def parm_search(self, obj, vars, temp_dict):
        if not vars:
            return

        for k,v in obj.items():
            if k in vars:
                temp_dict[k] = v
                vars.remove(k)
            elif isinstance(v, dict):
                self.parm_search(v, vars, temp_dict)

    """
    Convenience method.
    
    Rather than calling, obj.environment.get_templates(),
    call class instead.
    """
    def list_templates(self):
        return self.environment.list_templates()
    
    """
    Another convenience method.
    """
    def get_template(self, template_name, parent=None):
        return self.environment.get_template(template_name, parent=parent)
    
    """
    Creates prefix loader
    """
    def create_loader(self, root):
    
        directories = listdir(root)
        
        prefix_loader_dict = dict()
        
        for d in directories:
            prefix_loader_dict[d] = FileSystemLoader(join(root, d))
            
        return PrefixLoader(prefix_loader_dict)
        