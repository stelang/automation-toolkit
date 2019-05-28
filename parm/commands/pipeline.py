""" The pipeline command."""
from .base import Base

from parm import Parm
from parm.utilities import get_parm_file
from parm.pipelines import Jenkins
from parm.utilities import TemplateHandler, write_file, get_conf_file, get_parm_file

class Pipeline(Base):
    """Used for creating, updating, configuring tool agnostic CICD pipeline"""

    def run(self):
        parm = Parm(get_parm_file(self.options.get('<file>')))

        # create jenkins instance if condition exists in parm.yaml
        if not (parm.pipelines.get('jenkins')):
            print('No Jenkins condition specified, skipping')
        else:
            #get and write ansible group vars using jinja2
            th = TemplateHandler(parm)
            ansible = th.get_rendered_templates('ansible')
            write_file(get_conf_file('../../ansible/group_vars/all.yaml'), ansible[0])

            # instantiate jenkins object and create jenkins instance
            jenkins = Jenkins(parm)
            responseCode = jenkins.createJenkins()

            #if ansible fails, exit
            if responseCode != 0:
                print("Ansible failed while creating Jenkins, exiting")
                exit()
        
        