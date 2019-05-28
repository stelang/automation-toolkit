import json
import requests

"""
KibanaObject

Superclass of all other kibana object types.
"""
class KibanaObject(object):

    """
    Renaming of json.dumps()
    """
    def serialize(self, data):
        return json.dumps(data, ensure_ascii=False)
    
    """
    Renaming of json.loads()
    """
    def deserialize(self, string):
        return json.loads(string)
    
    """
    Parse method used to in the constructor of all objects.
    This will likely be moved to a higher object, ParmObject in future.
    """
    def parse(self, obj):
        for key, value in obj.items():
            if key in self.__dict__:
                setattr(self, key, value)
            if isinstance(value, dict):
                self.parse(value)

"""
KibanaManager class

Superclass of all other kibana manager types.

May consider making subclasses of this class generic...
"""                
class KibanaManager(object):
    
    """
    Takes in server name, appends uri needed to
    interact with the kibana api.
    """
    def __init__(self, server):
        self.server = f"{server}/api/saved_objects/"
    

    """
    Gets all kibana objects of the type specified in the subclass.
    
    Returns the response json of the get request. The response json 
    posesses a field, saved_objects, a list of all the objects of the
    requested type.
    """
    def get_all(self):
        
        headers = self.get_headers()
        
        url = f"{self.server}?per_page=1000"
        
        response = requests.get(url, verify=False, headers=headers)
        
        if response.status_code != requests.codes.ok:
            print(response.json())
        
        return response.json()
    
    """
    Posts object to kibana.
    
    If id specified, appends to url which specifies the
    id of the object within kibana. Otherwise, it'll post
    directly to kibana, and allow it to specify the id.
    """
    def post(self, data, id=None):
    
        headers = self.get_headers()
        
        url = self.server
        
        if 'id' is not None:
            url += '/%s' % id
        
        response = requests.post(url, verify=False, data=data, headers=headers)
        
        if response.status_code != requests.codes.ok:
            print(response.json())
            
        return response.json()

    def delete(self, id):
        headers = self.get_headers()

        url = f"{self.server}/{id}"

        response = requests.delete(url, verify=False, headers=headers)
        
    def get_headers(self):
        return { 
            'content-type': 'application/json',
            'kbn-xsrf': 'true'
        }