from subprocess import run
from os import getcwd
from parm.utilities import get_conf_file

"""
ELK Class

Used to provision and configure ELK using Ansible.

"""
class Elk(object):
    """
    parm object is passed for creating dict
    which will be used for creating ELK

    """
    def __init__(self, parm):
        self.parm = parm
    """
    Makes ansible call to create metricbeat index
    and install metricbeat on tagged hosts
    """
    def createELK(self):
        script = get_conf_file('../../ansible/scripts/install-elk.sh')
        ansiblePath = get_conf_file('../../ansible')
        return run([script, self.parm.product, ansiblePath, self.parm.aws['key_name']]).returncode