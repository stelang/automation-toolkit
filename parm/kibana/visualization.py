from .common import KibanaObject, KibanaManager
"""
Visualization Class

Takes in either a json, or string.

"""
class Visualization(KibanaObject):
    
    """
    String is converted to JSON.
    
    parse() is in parent class, KibanaObject.
    It recursively walks through nested dictionary structure passed in
    and fills out fields which are within the Visualization object.
    """
    def __init__(self, visualization):
        if isinstance(visualization, str):
            visualization = self.deserialize(visualization) 
        
        self.id = None
        self.title = None
        self.visState = None
        self.description = None
        self.uiStateJSON = None
        self.searchSourceJSON = None
        
        self.parse(visualization)
    
    """
    Prepares visualization object for posting.
    Creates the appropriate nested dictionary required,
    and stringifies it.
    """
    def to_kibana(self):
        
        payload = dict(attributes={})
        
        for key, value in self.__dict__.items():
            if key != 'id' and key !='searchSourceJSON':
                payload['attributes'][key] = value
            
            if key == 'searchSourceJSON':
                payload['attributes']['kibanaSavedObjectMeta'] = {}
                payload['attributes']['kibanaSavedObjectMeta'][key] = value
                
        return self.serialize(payload)
           
        
class VisualizationManager(KibanaManager):
    
    """
    Takes in server and appends visualization.
    This is common among all manager classes,
    and allows for interaction with kibana api.
    """
    def __init__(self, server):
        super().__init__(server)
        
        self.visualizations = None
        
        self.server += 'visualization'
        self.visualizations = dict()
    
    """
    Gets all visualizations in kibana, and assigns them to cache
    """
    def get_all(self):
        response = super().get_all()
        visualizations = dict()
        
        for obj in response['saved_objects']:
            vis = Visualization(obj)
            
            visualizations[vis.id] = vis
        
        self.visualizations = visualizations
    """
    Takes in a visualization object. If visualization 
    object posesses an id, the id of the posted 
    visualization will be that id, otherwise, it 
    will be randomly assigned one by kibana.
    """
    def add(self, visualization):
        response = self.post(visualization.to_kibana(), id=visualization.id)
        
        visualization = Visualization(response)
        
        self.visualizations[visualization.id] = visualization

    def delete(self, visualization):
        response = self.delete(visualization.id)

        if visualization.id in visualizations:
            del visualizations[visualization.id]

        return response

    def delete_all(self):
        if not visualizations:
            self.get_all()

        for k,v in visualizations.items():
            self.delete(k)

        visualizations = dict()
    