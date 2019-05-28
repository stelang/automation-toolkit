from subprocess import run
from os import getcwd
from parm.utilities import get_conf_file

"""
Metricbeat Class

Used to make metricbeat configurations.

"""
class Metricbeat(object):
    """
    parm object is passed for creating dict
    which will be used for createMetricbeatIndex

    """
    def __init__(self, parm):
        self.parm = parm
    """
    Makes ansible call to create metricbeat index
    and install metricbeat on tagged hosts
    """
    def createMetricbeatIndex(self):
        script = get_conf_file('../../ansible/scripts/install-metricbeat.sh')
        ansiblePath = get_conf_file('../../ansible')
        print('Inside createMetricbeatIndex Key name is ' + self.parm.aws['key_name'])
        return run([script, self.parm.product, ansiblePath, self.parm.aws['key_name']]).returncode
    """
    removes metricbeat from tagged hosts
    does not remove metricbeat index and pattern

    """
    def removeMetricbeat(self):
        print(getcwd())
        script = get_conf_file('../../ansible/scripts/remove-metricbeat.sh')
        print(script)
        ansiblePath = get_conf_file('../../ansible')
        print('Inside removeMetricbeat Key name is ' + self.parm.aws['key_name'])
        print('Inside removeMetricbeat profile is' + self.parm.aws['boto_profile'])
        return run([script, self.parm.product, ansiblePath, self.parm.aws['key_name']]).returncode