from subprocess import run
from os import getcwd
from parm.utilities import get_conf_file, write_file, render_template
import requests, time, json, jinja2, os, sys
from jinja2 import Environment  

"""
Newrelic API Wrapper Class

Used to configure Newrelic using Newrelic API.

"""
class Newrelic(object):
    """
    parm object is passed for creating payload
    for newrelic API calls

    """
    def __init__(self, parm):
        self.parm = parm
        self.account_name = self.FetchAccountID(parm.monitors.get('newrelic')['account_name'])
        print(self.account_name)
        self.admin_key = parm.monitors.get('newrelic')['admin_key']
        self.headerz = headerz = {'X-Api-Key': str(self.admin_key), 'Content-Type': 'application/json'}
        self.inc_pref = parm.monitors.get('newrelic')['inc_pref']
        self.pol_name = parm.monitors.get('newrelic')['pol_name']
        self.env = Environment()
    
    """
    Fetches Newrelic AccountID
    """
    def FetchAccountID(self, account_name):
        if account_name == 'cb non prod':
            return 1728023
        elif account_name == 'cb prod':
            return 1728024
        else:
            print("Invalid account name %s provided" % account_name)

    """
    Creates Newrelic Synthetics Monitor
    """
    def CreateSyntheticsMonitor(self, iName, iType, iFrequency, iURI, iLocations, iSlaT):
        api = 'https://synthetics.newrelic.com/synthetics/api/v3/monitors'
        payload = {    
            "name":iName,
            "type":iType,
            "status": "enabled",
            "frequency":iFrequency,
            "uri":iURI,
            "locations":iLocations,
            "slaThreshold": iSlaT
        }
        print("Creating Synthetics Monitor: " + str(iName))
        synthetics_req = requests.post(api, json=payload, headers=self.headerz)
        if synthetics_req.status_code == 201:
            print(str(iName) + ' was successfully created!')
            # print(synthetics_req.json())
            print("Sleeping...")
            time.sleep(5)
            print("...Up")
            monitorID = self.GetSyntheticsMonitorID(str(iName))
            print ("Synthetics Monitor: " + str(monitorID) + " successfully created.")
            if monitorID:
                self.AssignSyntheticsConditionToPolicy(str(iName), str(monitorID))
                #synthetics_response = synthetics_req.content
                #json_formatted= json.loads(synthetics_response)
                #monitorID = json_formatted['monitor']['id']
                #print(synthetics_req.content)
        else:
            print('Fail! Response code: ' + str(synthetics_req.status_code))
            print(synthetics_req.content)
    
    """
    Updates Newrelic Synthetics Monitor
    """
    def UpdateSyntheticsMonitor(self, mID, iName, iType, iFrequency, iURI, iLocations, iSlaT):
        api = 'https://synthetics.newrelic.com/synthetics/api/v3/monitors/%s' % mID
        payload = {    
            "name":iName,
            "type":iType,
            "status": "enabled",
            "frequency":iFrequency,
            "uri":iURI,
            "locations":iLocations,
            "slaThreshold": iSlaT
        }
        print("Updating Synthetics Monitor: %s" % iName)
        synthetics_req = requests.put(api, json=payload, headers=self.headerz)
        if synthetics_req.status_code == 204:
            print('Synthetics monitor %s was successfully updated!' % iName )
            # print(synthetics_req.json())
            print("Sleeping...")
            time.sleep(5)
            print("...Up")
            monitorID = self.GetSyntheticsMonitorID(str(iName))
            print ("Synthetics Monitor: %s successfully updated." % monitorID)
        else:
            print('Fail! Response code: %s' % synthetics_req.status_code)
            print(synthetics_req.content)
    
    """
    Deletes Newrelic Synthetics Monitor
    """
    def DeleteSyntheticsMonitor(self, mID, iName):
        api = 'https://synthetics.newrelic.com/synthetics/api/v3/monitors/%s' % mID
        print("Deleting Synthetics Monitor: %s" % iName)
        synthetics_req = requests.delete(api, headers=self.headerz)
        if synthetics_req.status_code == 204:
            print('Synthetics monitor %s was successfully deleted!' % iName )
        else:
            print('Fail! Response code: %s' % synthetics_req.status_code)
            print(synthetics_req.content)

    """
    Fetches Synthetics Monitor id
    """
    def GetSyntheticsMonitorID(self, aMonitorName):
        monitorslist = 'https://synthetics.newrelic.com/synthetics/api/v3/monitors'
        print("Getting Synthetics Monitor ID for: " + str(aMonitorName))
        # payload = {'filter[name]': str(anAppName)}
        r = requests.get(monitorslist, headers=self.headerz)
        if r.status_code == 200:
            monitors = r.json()
            for monitor in monitors['monitors']:
                if str(aMonitorName) in monitor['name']:
                    mID = monitor['id']
                    # print ("Monitor ID: " + monitor['id'])
                    return mID
        else:
            print ("Error! Status code: " + r.status_code)
            print (r.content)
    
    """
    Creates new alerts policy
    """
    def CreateNewPolicy(self, ip, pn):
        global polID #assign as global so we can modify the var
        payload1 = {
            "policy": {
                "incident_preference": ip,
                "name": pn
            }
        }
        print ("Creating Policy: %s" % pn)
        pol_url = 'https://api.newrelic.com/v2/alerts_policies.json'
        policyCreate = requests.post(pol_url, data=json.dumps(payload1), headers=self.headerz)
        if policyCreate.status_code == 201:
            pol_response = policyCreate.content
            json_formatted= json.loads(pol_response)
            polID = json_formatted['policy']['id']
            print ("Policy Number: %s successfully created. Storing ID" % polID)
            return polID
        else:
            print("Status Code: %s" % policyCreate.status_code)
            print("Policy Creation Failed!")
            print(policyCreate.content)  
    
    """
    Creates infra conditions
    """
    def CreateInfraCondition(self, iType, iName, iFilter, ieType, iValue, iCompare, iCrit, iWarn, iCritD, iWarnD):
        api = 'https://infra-api.newrelic.com/v2/alerts/conditions'
        payload = {
            "data":{
                "type":iType,
                "name":iName,
                "enabled": bool("true"),
                "where_clause": iFilter,
                "policy_id": polID,
                "event_type":ieType,
                "select_value":iValue,
                "comparison":iCompare,
                "critical_threshold":{
                    "value": iCrit,
                    "duration_minutes": iCritD,
                    "time_function":"all" #can be all or any-- all= "for at least", any = "at least once in"
                },
                "warning_threshold":{
                    "value": iWarn,
                    "duration_minutes": iWarnD,
                    "time_function":"all"
                }
            }
        }

        print ("Creating Infrastructure Condition: %s" % iName)
        infra_req = requests.post(api, json=payload, headers=self.headerz)
        if infra_req.status_code == 201:
            print('%s was successfully created!' % iName)
        else:
            print('Fail! Response code: %s' % infra_req.status_code)
            print(infra_req.content)
    """
    Assigns Synthetics monitor to Alert policy
    """
    def AssignSyntheticsConditionToPolicy(self, aMonitorName, aMonitorID):
        print ("Assigning Synthetics condition to policy...")
        api = 'https://api.newrelic.com/v2/alerts_synthetics_conditions/policies/' + str(polID) + '.json'
        payload = {
            "synthetics_condition": { 
                "name": aMonitorName, 
                "monitor_id": aMonitorID,
                "enabled": bool("true")
            }
        }
        r = requests.post(api, headers=self.headerz, json=payload)
        if str(r.status_code)[:1] == '2':
            print ("Success! Synthetics with ID: " + str(aMonitorID) +" is attached!")
            print (r.content)
        else:
            print ("Failed with status code: " + str(r.status_code))
            print (r.content)
    
    """
    Creates user defined APM condition
    """
    def CreateUserDefinedCondition(self, metricType, condTitle, condMetric, condDuration, condCriticalT, condWarnT, condOperator, userMetric, userValue):
        api = 'https://api.newrelic.com/v2/alerts_conditions/policies/' + str(polID) + '.json' #policy ID used here to assign conditions
        payload = {
            "condition": {
                "type": metricType,
                "name": condTitle,
                "enabled": "true",
                "condition_scope": "application",
                "entities": [

                ],
            "metric": condMetric,
            "violation_close_timer": "8",
            "terms": [
            {
                "duration": str(condDuration),
                "operator": condOperator,
                "priority": "critical",
                "threshold": str(condCriticalT),
                "time_function": "all"
            },
            {
                "duration": str(condDuration),
                "operator": condOperator,
                "priority": "warning",
                "threshold": str(condWarnT),
                "time_function": "all"
            }],
                "user_defined": {
                    "metric": str(userMetric),
                    "value_function": str(userValue)
                }
            }
        }

      # post condition
        print ("Creating User Defined Condition: " + str(condTitle))
        apm_req = requests.post(api, json=payload, headers=self.headerz)
        if apm_req.status_code == 201:
            print(condTitle + ' was successfully created!')
            resp = apm_req.json()
            if resp['condition']['type'] in ('apm_app_metric', 'apm_kt_metric'):
                anID = resp['condition']['id']
                return anID
            else:
                print ("Unknown condition type!")
        else:
            print('Fail! Response code: ' + str(apm_req.status_code))
            print (apm_req.content)
    
    """
    Creates APM condition
    """
    def CreateAPMCondition(self, metricType, condTitle, condMetric, condDuration, condCriticalT, condWarnT, condOperator):
        api = 'https://api.newrelic.com/v2/alerts_conditions/policies/' + str(polID) + '.json' #policy ID used here to assign conditions
        
        payload = {
            "condition": {
                "type": metricType,
                "name": condTitle,
                "enabled": "true",
                "condition_scope": "application",
                "entities": [

                ],
            "metric": condMetric,
            "violation_close_timer": "8",
            "terms": [
            {
                "duration": str(condDuration),
                "operator": condOperator,
                "priority": "critical",
                "threshold": str(condCriticalT),
                "time_function": "all"
            },
            {
                "duration": str(condDuration),
                "operator": condOperator,
                "priority": "warning",
                "threshold": str(condWarnT),
                "time_function": "all"
            }]
            }
        }

        if 'gc_cpu_time' in condMetric:
            payload['condition']['gc_metric'] = "GC/G1 Young Generation"

    # post condition
        print ("Creating APM Condition: " + str(condTitle))
        # json_payload = json.dumps(payload)
        apm_req = requests.post(api, json=payload, headers=self.headerz)
        if apm_req.status_code == 201:
            print(condTitle + ' was successfully created!')
            resp = apm_req.json()
            if resp['condition']['type'] in ('apm_app_metric', 'apm_kt_metric', 'apm_jvm_metric'):
                anID = resp['condition']['id']
                return anID
            else:
                print ("Unknown condition type!")
        else:
            print('Fail! Response code: ' + str(apm_req.status_code))
            print(apm_req.content)
    
    """
    Gets APM Entity ID
    """
    def GetAPMEntityID(self, anAppName):
        entityapm = 'https://api.newrelic.com/v2/applications.json'
        print("Getting APM Entity ID for: " + str(anAppName))
        payload = {'filter[name]': str(anAppName)}
        r = requests.get(entityapm, headers=self.headerz, params=payload)
        if r.status_code == 200:
            response = r.json()
            id = response['applications'][0]['id']
            return id
        else:
            print ("Error! Status code: " + r.status_code)
            print (r.content)
    
    """
    Assigns APM Entity to APM condition
    """
    def AssignAPMEntityToCondition(self, aConditionID, aentityID):
        print ("Assigning defined APM entity to condition...")
        api = 'https://api.newrelic.com/v2/alerts_entity_conditions/' + str(aentityID) + '.json'
        payload = {'entity_type': 'Application', 'condition_id': aConditionID}
        r = requests.put(api, headers=self.headerz, params=payload)
        if str(r.status_code)[:1] == '2':
            print ("Success! Application entity: " + str(aentityID) +" assigned!")
        else:
            print ("Failed with status code: " + str(r.status_code))
            print (r.content)
    
    """
    Assigns Channels
    """
    def AssignChannels(self, emailsToAdd):
        api = 'https://api.newrelic.com/v2/alerts_policy_channels.json'
        channelIDs = self.getChannelIDs()
        emailList = []
        try:
            print ("Adding channels to policy for desired emails")
            headerz = {'X-Api-Key': self.admin_key}
            for email in emailsToAdd:
                if email in channelIDs.keys():
                    emailList.append(channelIDs[email]) #add id to var based on email(key)
                else:
                    print ('Email ' + str(email) + ' not found, attempting to create channel...')
                    newEmailID = self.CreateEmailChannel(email)
                    emailList.append(newEmailID) # add newly created ID to list of channels to add to policy
            emailString = ",".join([str(x) for x in emailList]) # create comma sep list
            payload = {"policy_id": str(polID), "channel_ids": str(emailString)}
            r = requests.put(api,headers=headerz,params=payload)
            if str(r.status_code)[:1] == '2':
                resp = r.json()
                print ("Added emails successfully!")
            else:
                print ("Error Occurred: " + str(r.status_code))
                print (r.content)
        except IndexError:
            return 'ER'
    
    """
    Creates Email Channel
    """
    def CreateEmailChannel(self, email):
        endpoint = 'https://api.newrelic.com/v2/alerts_channels.json'
        emailPayload = {
                "channel": {
                "name": str(email),
                "type": "email",
                "configuration": {
                    "recipients": str(email),
                    "include_json_attachment": bool("true")
                    }
                }
        }
        try:
            r = requests.post(endpoint, headers=self.headerz, json=emailPayload)
            if str(r.status_code)[:1] == '2':
                resp = r.json()
                newID = resp['channels'][0]['id'] #store ID of new channel created
                return newID #return ID to assign to current policy
        except IndexError:
            return 'ER'
    
    """
    Assigns PD channel to alert policy
    """
    def AssignPDChanneltoPolicy(self, pdTitle, pdKey):
        try:
            print ("Adding PagerDuty Channel to policy...")
            api = 'https://api.newrelic.com/v2/alerts_policy_channels.json'
            headerz = {'X-Api-Key': self.admin_key}
            pdID = self.CreatePagerDutyChannel(pdTitle, pdKey)
            payload = {"policy_id": str(polID), "channel_ids": str(pdID)}
            r = requests.put(api, headers=headerz, params=payload)
            if str(r.status_code)[:1] == '2':
                resp = r.json()
                print ("Added PagerDuty Channel successfully!")
            else:
                print ("Error Occurred: " + str(r.status_code))
                print (r.content)
        except IndexError:
            return 'ER'
    
    """
    Create Pager Duty channel within newrelic
    """
    def CreatePagerDutyChannel(self, pdTitle, pdKey):
        endpoint = 'https://api.newrelic.com/v2/alerts_channels.json'
        pdPayload = {
                "channel": {
                "name": str(pdTitle),
                "type": "pagerduty",
                "configuration": {
                    "service_key": str(pdKey)
                    }
                }
        }
        try:
            r = requests.post(endpoint, headers=self.headerz, json=pdPayload)
            if str(r.status_code)[:1] == '2':
                resp = r.json()
                newPDID = resp['channels'][0]['id'] #store ID of new channel created
                return newPDID #return ID to assign to current policy
        except IndexError:
            return 'ER'
    
    """
    Assigns Slack channel to alert policy
    """
    def AssignSlackChanneltoPolicy(self, slkTitle, slkURL, slkChannel):
        try:
            print ("Adding Slack Channel to policy...")
            api = 'https://api.newrelic.com/v2/alerts_policy_channels.json'
            headerz = {'X-Api-Key': self.admin_key}
            slkID = self.CreateSlackChannel(slkTitle, slkURL, slkChannel)
            payload = {"policy_id": str(polID), "channel_ids": str(slkID)}
            r = requests.put(api, headers=headerz, params=payload)
            if str(r.status_code)[:1] == '2':
                resp = r.json()
                print ("Added Slack Channel successfully!")
            else:
                print ("Error Occurred: " + str(r.status_code))
                print (r.content)
        except IndexError:
            return 'ER'
    
    """
    Create Slack channel within newrelic
    """
    def CreateSlackChannel(self, slkTitle, slkURL, slkChannel):
        endpoint = 'https://api.newrelic.com/v2/alerts_channels.json'
        pdPayload = {
                "channel": {
                "name": str(slkTitle),
                "type": "slack",
                "configuration": {
                    "url": str(slkURL) ,
                    "channel": str(slkChannel)
                    }
                }
        }
        try:
            r = requests.post(endpoint, headers=self.headerz, json=pdPayload)
            if str(r.status_code)[:1] == '2':
                resp = r.json()
                newSlackID = resp['channels'][0]['id'] #store ID of new channel created
                return newSlackID #return ID to assign to current policy
        except IndexError:
            return 'ER'
    
    """
    Fetches channel IDs
    """
    def getChannelIDs(self):
        api = 'https://api.newrelic.com/v2/alerts_channels.json'
        head = {'X-Api-Key': self.admin_key}
        cycle = 0
        try_again = 1
        first_time = 1
        channel_dict = {} #key value lookup for email-id
        try:
            print ('Obtaining Channel IDs...')
            while try_again == 1:
                payload = {'page': cycle}
                r = requests.get(api, headers=head, params=payload)
                print ('Requesting Channels Status Code= ' + str(r.status_code) + '\nCycle: ' + str(cycle))
                channels = r.json()
                if str(r.status_code)[:1] == '2':
                    cycle+=1 
                    for aChannel in channels['channels']:
                        if 'email' in aChannel['type']:
                            email = aChannel['name']
                            nID = aChannel['id']
                            channel_dict.update({email: nID})
                    if 'last' not in r.links:
                        try_again = 0
                elif str(r.status_code)[:1] == '4':
                    print("Error! Invalid request-Check API key or inputs")
                else:
                    print("Could not complete request.")
            return channel_dict
        except IndexError:
            return 'ER'
    
    """
    Creates Dashboard
    """
    def CreateDashboard(self, dNames, dTitle):
        api = 'https://api.newrelic.com/v2/dashboards.json'
        apps = ', '.join("'{0}'".format(d) for d in dNames)
        params = {
            'apps': apps,
            'accountID': self.account_name,
            'title': dTitle
        }
        payload = render_template("newrelic/payload.json", params)
        print(payload)
        print ("Creating Dashboard: %s" % dNames)
        dash_req = requests.post(api, json=json.loads(payload), headers=self.headerz)
        if dash_req.status_code == 200:
            print('%s was successfully created!' % dNames)
        else:
            print('Fail! Response code: %s' % dash_req.status_code)
            print(dash_req.content)