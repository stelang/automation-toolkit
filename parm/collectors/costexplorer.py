from subprocess import run
from os import getcwd
from parm.utilities import get_conf_file
import boto3, datetime, json, functools, operator, time
from botocore.exceptions import ClientError

"""
AWS Cost Explorer Class

Used to get cost explorer data and post to ES.

"""
class Costexplorer(object):
    """
    parm object is passed for creating dict

    """
    def __init__(self, parm, profile=None):

        if profile:
            self.session = boto3.session.Session(profile_name=profile)
        else:
            self.session = boto3.session.Session()

        self.parm = parm
        self.costexplorerClient = self.session.client('ce')

    """
    Wrapper for boto3 get cost and usage service
    """
    def get_cost_and_usage(self, linkedAccount, i, j):
        end_time = ((datetime.datetime.today() - datetime.timedelta(int(i)))).strftime('%Y-%m-%d')
        start_time = (datetime.date.today() - datetime.timedelta(int(j))).isoformat()
        TimePeriod = {"Start": start_time, "End": end_time}
        Granularity = "DAILY"
        Filter = {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": [str(linkedAccount)]}}
        GroupBy = [{"Type": "DIMENSION", "Key": "SERVICE"}]
        Metrics = ["UnblendedCost"]
        
        # get costs grouped by service for specified aws account for the last day
        response = self.costexplorerClient.get_cost_and_usage(TimePeriod = TimePeriod, Granularity = Granularity, Filter = Filter, GroupBy = GroupBy, Metrics = Metrics) 
        dict1 = {k : v for k,v in filter(lambda t: t[0] in ['ResultsByTime'], response.items())}
        l = dict1.get('ResultsByTime')[0].get('Groups')
        keys = [d['Keys'] for d in l if 'Keys' in d]
        keys_flat = [item for sublist in keys for item in sublist]
        metrics = [d['Metrics'] for d in l if 'Metrics' in d]
        
        unblendeds = [d['UnblendedCost'] for d in metrics if 'UnblendedCost' in d]
        amounts = [d['Amount'] for d in unblendeds if 'Amount' in d]

        costDict = dict(zip(keys_flat,amounts))
        costDict['@timestamp'] = ((datetime.datetime.today() - datetime.timedelta(int(j)))).strftime('%Y-%m-%d %H:%M:%S')

        return costDict

        
