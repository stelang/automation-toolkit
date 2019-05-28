""" The cleanup command."""
from .base import Base

from parm import Parm
from parm.utilities import TemplateHandler, write_file, get_conf_file, get_parm_file
from parm.collectors import Metricbeat
from parm.kibana import Kibana

class Cleanup(Base):
    """makes E + K squeaky clean"""

    def run(self):
        # get latest parm object
        parm = Parm(get_parm_file(self.options.get('<file>')))

        # delete all kibana saved objects
        kibana = Kibana(parm)
        kibana.delete_all()

        # remove metricbeat from tagged EC2s
        th = TemplateHandler(parm)
        ansible = th.get_rendered_templates('ansible')
        write_file(get_conf_file('../../ansible/group_vars/all.yaml'), ansible[0])
        mb = th.get_rendered_templates('metricbeat')
        write_file(get_conf_file('../../output/metricbeat.yml'), mb[0])
        metricbeat = Metricbeat(parm)
        responseCode = metricbeat.removeMetricbeat()

        if responseCode != 0:
                print("Ansible failed, exiting")
                exit()

        