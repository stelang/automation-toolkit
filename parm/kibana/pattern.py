from .common import KibanaObject, KibanaManager
"""
IndexPattern Class

Takes in either a json, or string.

"""
class IndexPattern(KibanaObject):
    
    """
    String is converted to JSON.
    
    parse() is in parent class, KibanaObject.
    It recursively walks through nested dictionary structure passed in
    and fills out fields which are within the index-pattern object.
    """
    def __init__(self, index_pattern):
        if isinstance(index_pattern, str):
            index_pattern = self.deserialize(index_pattern)
        
        self.id = None
        self.title = None
        self.timeFieldName = None
        self.fields = None
        
        self.parse(index_pattern)
    
    """
    Prepares index-pattern object for posting.
    Creates the appropriate nested dictionary required,
    and stringifies it.
    """    
    def to_kibana(self):
        
        payload = dict(attributes={})
        
        payload['attributes']['title'] = self.title
        
        if self.timeFieldName is not None:
            payload['attributes']['timeFieldName'] = self.timeFieldName
        
        return self.serialize(payload)
        
class IndexPatternManager(KibanaManager):
    
    """
    Takes in server and appends index-pattern.
    This is common among all manager classes,
    and allows for interaction with kibana api.
    """
    def __init__(self, server):
        super().__init__(server)
        
        self.patterns = None
        
        self.server += 'index-pattern'
        self.patterns = dict()
    
    """
    Takes in a index-pattern object. If index-pattern 
    object posesses an id, the id of the posted 
    index-pattern will be that id, otherwise, it 
    will be randomly assigned one by kibana.
    """
    
    """
    Gets all index-patterns in kibana, and assigns them to cache
    """
    def get_all(self):
        response = super().get_all()
        
        patterns = dict()
        
        for obj in response['saved_objects']:
            pattern = IndexPattern(obj)
            
            patterns[pattern.id] = pattern
        
        self.patterns = patterns
        
    def add(self, pattern):
        response = self.post(pattern.to_kibana(), id=pattern.id)
        
        pattern = IndexPattern(response)
        
        self.patterns[pattern.id] = pattern

    def delete(self, pattern):
        response = self.delete(pattern.id)

        if pattern.id in patterns:
            del patterns[pattern.id]

        return response

    def delete_all(self):
        if not patterns:
            self.get_all()

        for k,v in patterns.items():
            self.delete(k)

        patterns = dict()