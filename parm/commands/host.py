""" The cleanup command."""
from .base import Base

from parm import Parm
from parm.utilities import get_parm_file
from parm.ecs import ECS

class Host(Base):
    """makes E + K squeaky clean"""

    def run(self):
        parm = Parm(get_parm_file(self.options.get('<file>')))
        
        ecs = ECS(parm)
        ecs.host_all()