from .common import KibanaObject, KibanaManager
"""
Dashboard Class

Takes in either a json, or string.

"""
class Dashboard(KibanaObject):
      
    """
    String is converted to JSON.
    
    parse() is in parent class, KibanaObject.
    It recursively walks through nested dictionary structure passed in
    and fills out fields which are within the Dashboard object.
    """
    def __init__(self, dashboard):
        if isinstance(dashboard, str):
            dashboard = self.deserialize(dashboard)
        
        self.id = None
        self.title = None
        self.description = None
        self.panelsJSON = None
        self.optionsJSON = None
        self.searchSourceJSON = None
        self.uiStateJSON = None
        
        self.parse(dashboard)
    
    """
    Prepares dashboard object for posting.
    Creates the appropriate nested dictionary required,
    and stringifies it.
    """
    def to_kibana(self):
    
        payload = dict(attributes={})
        
        for key, value in self.__dict__.items():
            if key != 'id' and key != 'searchSourceJSON':
                payload['attributes'][key] = value
            
            if key == 'searchSourceJSON':
                payload['attributes']['kibanaSavedObjectMeta'] = {}
                payload['attributes']['kibanaSavedObjectMeta'][key] = value
            
        return self.serialize(payload)
        
class DashboardManager(KibanaManager):
    
    """
    Takes in server and appends dashboard.
    This is common among all manager classes,
    and allows for interaction with kibana api.
    """
    def __init__(self, server):
        super().__init__(server)
        
        self.dashboards = None
        
        self.server += 'dashboard'
        self.dashboards = dict()
    
    """
    Gets all dashboards in kibana, and assigns them to cache
    """
    def get_all(self):
        response = super().get_all()
        
        dashboards = dict()
        
        for obj in response['saved_objects']:
            dash = Dashboard(obj)
            
            dashboards[dash.id] = dash
        
        self.dashboards = dashboards
            
    """
    Takes in a dashboard object. If dashboard 
    object posesses an id, the id of the posted 
    dashboard will be that id, otherwise, it 
    will be randomly assigned one by kibana.
    """
    def add(self, dashboard):
        response = self.post(dashboard.to_kibana(), id=dashboard.id)
        
        dashboard = Dashboard(response)
        
        self.dashboards[dashboard.id] = dashboard

    def delete(self, dashboard):
        response = self.delete(dashboard.id)

        if dashboard.id in dashboards:
            del dashboards[dashboard.id]

        return response

    def delete_all(self):
        if not dashboards:
            self.get_all()

        for k,v in dashboards.items():
            self.delete(k)

        dashboards = dict()