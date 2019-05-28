from subprocess import run
from os import getcwd
from parm.utilities import get_conf_file

"""
Jenkins Class

Used to provision and configure Jenkins using Ansible.

"""
class Jenkins(object):
    """
    parm object is passed for creating dict
    which will be used for creating Jenkins

    """
    def __init__(self, parm):
        self.parm = parm
    """
    Makes ansible call to provision and configure Jenkins
    """
    def createJenkins(self):
        script = get_conf_file('../../ansible/scripts/jenkins.sh')
        ansiblePath = get_conf_file('../../ansible')
        return run([script, self.parm.product, ansiblePath, self.parm.aws['key_name']]).returncode