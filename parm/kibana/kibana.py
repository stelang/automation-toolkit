from .pattern import IndexPatternManager
from .visualization import VisualizationManager
from .dashboard import DashboardManager
from progressbar import ProgressBar

import requests

class Kibana(object):
    
    def __init__(self, parm):
        self.parm = parm
        self.endpoint = 'http://%s-elk.%s:5601' %(parm.get_property('boto_profile', nested='aws'),parm.get_property('zone', nested='aws'))
        self.indexPatternManager = IndexPatternManager(self.endpoint)
        self.visualizationManager = VisualizationManager(self.endpoint)
        self.dashboardManager = DashboardManager(self.endpoint)
        
    
    @property
    def indexPatterns(self):
        if self.indexPatternManager.patterns == {}:
            self.indexPatternManager.get_all()
        
        return self.indexPatternManager.patterns
        
    @indexPatterns.setter
    def indexPatterns(self, indexPatterns):
        self.indexPatternManager.patterns = indexPatterns

    @indexPatterns.deleter
    def indexPatterns(self):
        self.indexPatternManager.delete_all()

    @property
    def visualizations(self):
        if self.visualizationManager.visualizations == {}:
            self.visualizationManager.get_all()
        
        return self.visualizationManager.visualizations
        
    @visualizations.setter
    def visualizations(self, visualizations):
        self.visualizationManager.visualizations = visualizations
    
    @visualizations.deleter
    def visualizations(self):
        self.visualizationManager.delete_all()

    @property
    def dashboards(self):
        if self.dashboardManager.dashboards == {}:
            self.dashboardManager.get_all()
        
        return self.dashboardManager.dashboards
        
    @dashboards.setter
    def dashboards(self, dashboards):
        self.dashboardManager.dashboards = dashboards

    @dashboards.deleter
    def visualizations(self):
        self.dashboardManager.delete_all()
   
    def add_pattern(self, pattern):
        self.indexPatternManager.add(pattern)
    
    def add_visualization(self, visualization):
        self.visualizationManager.add(visualization)
    
    def add_dashboard(self, dashboard):
        self.dashboardManager.add(dashboard)
        
    def update_pattern(self, pattern):
        pass
    
    def update_visualization(self, visualization):
        pass
    
    def update_dashboard(self, dashboard):
        pass
    
    def delete_pattern(self, pattern):
        self.indexPatternManager.delete(pattern)
    
    def delete_visualization(self, visualization):
        self.visualizationManager.delete(pattern)
    
    def delete_dashboard(self, dashboard):
        self.dashboardManager.delete(pattern)

    def delete_all(self):
        url = f"{self.endpoint}/api/saved_objects"
        print('Cleaning up this baby --> ' + url)
        headers = self.get_headers()

        response = requests.get(f"{url}?per_page=10000", verify=False, headers=headers).json()
        pbar = ProgressBar()
        for obj in pbar(response['saved_objects']):
            _id = obj['id']
            _type= obj['type']

            del_url = f"{url}/{_type}/{_id}"

            requests.delete(del_url, verify=False, headers=headers)

    def get_headers(self):
        return { 
            'content-type': 'application/json',
            'kbn-xsrf': 'true'
        }


