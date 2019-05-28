from yaml import load
import argparse

class Parm(object):
    def __init__(self, file):
        self._product = None
        self._environment = None
        self._collectors = None
        self._aws = None
        self._ecs = None
        self._cmdb = None
        self._monitors = None
        self._pipelines = None
        self.parm_parse(file)
    
    @property
    def product(self):
        return self._product
    
    @product.setter
    def product(self, product):
        if not product:
            self._product = "default"
        else:
            self._product = product
        return self._product
    
    @property
    def environment(self):
        return self._environment
    
    @environment.setter
    def environment(self, environment):
        if not environment:
            self._environment = "dev"
        else:
            self._env = environment
        return self._environment
    
    @property
    def collectors(self):
        return self._collectors
    
    @collectors.setter
    def collectors(self, collectors):
        self._collectors = collectors

    @property
    def aws(self):
        return self._aws
    
    @aws.setter
    def aws(self, aws):
        self._aws = aws

    @property
    def ecs(self):
        return self._ecs

    @ecs.setter
    def ecs(self, ecs):
        self._ecs = ecs
    
    @property
    def cmdb(self):
        return self._cmdb

    @cmdb.setter
    def cmdb(self, cmdb):
        self._cmdb = cmdb
    
    @property
    def monitors(self):
        return self._monitors

    @monitors.setter
    def monitors(self, monitors):
        self._monitors = monitors
    
    @property
    def pipelines(self):
        return self._pipelines

    @pipelines.setter
    def pipelines(self, pipelines):
        self._pipelines = pipelines
    
    def get_property(self, key, nested=None):
        if nested == None:
            return getattr(self, key)
        else:
            dict = getattr(self, nested)
            return dict[key]
    
    def parm_parse(self, file):
        try:
            with open(file, 'r') as stream:
                parm = load(stream)
                self.parse(parm)
        except IOError as e:
            print("File doesn't exist")
    
    def parse(self, obj):
        for key, value in obj.items():
            key = "_" + key
            
            if key in self.__dict__:
                setattr(self, key, value)
    