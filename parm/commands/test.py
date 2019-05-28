from .base import Base

from parm import Parm
from parm.utilities import TemplateHandler, get_parm_file

class Test(Base):

    def run(self):
        loc = get_parm_file(self.options.get('<file>'))
        parm = Parm(loc)