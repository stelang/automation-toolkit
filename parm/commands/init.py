""" The init command."""
from .base import Base
from parm.utilities import Initializer

class Init(Base):

    """Generates initially needed files and configurations for user"""
    def run(self):    
        init = Initializer()
        init.initialize()