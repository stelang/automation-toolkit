""" The monitors command."""
from .base import Base

from parm import Parm
from parm.utilities import TemplateHandler, write_file, get_conf_file, get_parm_file
from parm.monitors import Elk, Newrelic

class Monitors(Base):
    """makes monitors specified in parm.yaml"""

    def run(self):
        parm = Parm(get_parm_file(self.options.get('<file>')))

        # Global assignments
        global admin_key
        global inc_pref
        global pol_name
        global account_name
        admin_key = parm.monitors.get('newrelic')['admin_key']
        account_name = parm.monitors.get('newrelic')['account_name']
        inc_pref = parm.monitors.get('newrelic')['inc_pref']
        pol_name = parm.monitors.get('newrelic')['pol_name']
        eAdd = parm.monitors.get('newrelic')['emails_to_add']
        pdTitle = parm.monitors.get('newrelic')['pagerduty_title']
        pdKey = parm.monitors.get('newrelic')['pagerduty_key']
        slkTitle = parm.monitors.get('newrelic')['slack_title']
        slkURL = parm.monitors.get('newrelic')['slack_url']
        slkChannel = parm.monitors.get('newrelic')['slack_channel']

        # ELK stuff
        # create elk instance if condition exists in parm.yaml
        if (parm.monitors.get('elk')) != 'create':
            print('No ELK condition specified, skipping')
        else:
            #get and write ansible group vars using jinja2
            th = TemplateHandler(parm)
            ansible = th.get_rendered_templates('ansible')
            write_file(get_conf_file('../../ansible/group_vars/all.yaml'), ansible[0])

            # instantiate Elk object and create ELK instance
            elk = Elk(parm)
            responseCode = elk.createELK()

            #if ansible fails, exit
            if responseCode != 0:
                print("Ansible failed, exiting")
                exit()
        
        # Newrelic stuff
        newrelic = Newrelic(parm)
        #Check if any vars missing-- if no, create policy
        if not all((admin_key, inc_pref, pol_name, account_name)):
            print ("Missing a config value! Please verify parm.yaml")
            exit(1)
        else:
            newrelic.CreateNewPolicy(inc_pref, pol_name)
        
        # create/update/delete newrelic synthetics if condition exists in parm.yaml
        synthetics_conds = parm.monitors.get('newrelic')['synthetics']['synthetics_condition_names']
        if not synthetics_conds:
            print ("No SYNTHETICS conditions specified, skipping...")
        else:
            s = 0
            sName = parm.monitors.get('newrelic')['synthetics']['synthetics_condition_names']
            sType = parm.monitors.get('newrelic')['synthetics']['synthetics_type']
            sFrequency = parm.monitors.get('newrelic')['synthetics']['synthetics_frequency']
            sUri = parm.monitors.get('newrelic')['synthetics']['synthetics_uri']
            sLocations = parm.monitors.get('newrelic')['synthetics']['synthetics_locations']
            sSlaThreshold = parm.monitors.get('newrelic')['synthetics']['synthetics_slaThreshold']
            action = parm.monitors.get('newrelic')['synthetics']['action']
            if action == 'create':
                while s < len(synthetics_conds):
                    newrelic.CreateSyntheticsMonitor(sName[s], sType[s], sFrequency[s], sUri[s], sLocations[s], sSlaThreshold[s])
                    s +=1
            elif action == 'update':
                while s < len(synthetics_conds):
                    mID = newrelic.GetSyntheticsMonitorID(sName[s])
                    if mID:
                        newrelic.UpdateSyntheticsMonitor(mID, sName[s], sType[s], sFrequency[s], sUri[s], sLocations[s], sSlaThreshold[s])
                    else:
                        print ("Monitor with name %s does not exist, cannot update" % sName[s])
                    s +=1
            elif action == 'delete':
                while s < len(synthetics_conds):
                    mID = newrelic.GetSyntheticsMonitorID(sName[s])
                    if mID:
                        newrelic.DeleteSyntheticsMonitor(mID, sName[s])
                    else:
                        print ("Monitor with name %s does not exist, cannot delete" % sName[s])
                    s +=1
        
        # create newrelic infra conditions, if condition exists in parm.yaml
        infra_conds = parm.monitors.get('newrelic')['infra']['infra_condition_names']
        if not infra_conds:
            print ("No Infrastructure conditions specified, skipping...")
        else:
            p = 0
            pType = parm.monitors.get('newrelic')['infra']['metric_types']
            pNames = parm.monitors.get('newrelic')['infra']['infra_condition_names']
            peType = parm.monitors.get('newrelic')['infra']['eventType']
            pFilter = parm.monitors.get('newrelic')['infra']['filterClause']
            pValue = parm.monitors.get('newrelic')['infra']['selectValue']
            pCompare = parm.monitors.get('newrelic')['infra']['infra_comparison']
            pCrit = parm.monitors.get('newrelic')['infra']['criticalT']
            pWarn = parm.monitors.get('newrelic')['infra']['warningT']
            pCritD = parm.monitors.get('newrelic')['infra']['crit_durations']
            pWarnD = parm.monitors.get('newrelic')['infra']['warn_durations']
            while p < len(infra_conds):
                newrelic.CreateInfraCondition(pType[p], pNames[p], pFilter[p], peType[p], pValue[p], pCompare[p], pCrit[p], pWarn[p], pCritD[p], pWarnD[p])
                p +=1

        
        # create newrelic APM conditions, if condition exists in parm.yaml
        apm_conds = parm.monitors.get('newrelic')['apm']['apm_condition_names']
        if not apm_conds:
            print ("No APM conditions specified, skipping...")
        else:
            k = 0
            app_names = parm.monitors.get('newrelic')['apm']['app_names'] # ***THIS SHOULD MATCH APP_NAMES CONFIGURED IN APM AGENT YML
            mType = parm.monitors.get('newrelic')['apm']['metric_types']
            cNames = parm.monitors.get('newrelic')['apm']['apm_condition_names']
            cMetrics = parm.monitors.get('newrelic')['apm']['apm_condition_metrics']
            cDurations = parm.monitors.get('newrelic')['apm']['apm_condition_duration']
            cCrit = parm.monitors.get('newrelic')['apm']['apm_condition_critT']
            cWarn = parm.monitors.get('newrelic')['apm']['apm_condition_warnT']
            cOps = parm.monitors.get('newrelic')['apm']['apm_cond_operators']
            userMetric = parm.monitors.get('newrelic')['apm']['apm_custom_metrics']
            userValue = parm.monitors.get('newrelic')['apm']['apm_value_functions']
            while k < len(apm_conds):
                x=0 #counter for looping through applications to assign to policies.
                z=0 #counter for custom metrics- dependent on if 'user_defined' is specified in apm_condition_metrics
                if cMetrics[k] == 'user_defined':
                    aConditionID = newrelic.CreateUserDefinedCondition(mType[k], cNames[k], cMetrics[k], cDurations[k], cCrit[k], cWarn[k], cOps[k], userMetric[z], userValue[z])
                    z+=1
                else:
                    aConditionID = newrelic.CreateAPMCondition(mType[k], cNames[k], cMetrics[k], cDurations[k], cCrit[k], cWarn[k], cOps[k])
                while x < len(app_names):
                    aentityID = newrelic.GetAPMEntityID(app_names[x])
                    newrelic.AssignAPMEntityToCondition(aConditionID, aentityID)
                    x+=1
                k+=1
        
        #Assign channels to policies if not blank in config
        if eAdd == []:
            print ("No email notification channels to add! Skipping...")
        else:
            newrelic.AssignChannels(eAdd)

        if (not str(pdTitle) and not str(pdKey)):
            newrelic.AssignPDChanneltoPolicy(pdTitle, pdKey)
        else:
            print ("No PagerDuty channels to add! Skipping...")


        if (not str(slkTitle) and not str(slkURL) and not str(slkChannel)):
            newrelic.AssignSlackChanneltoPolicy(slkTitle, slkURL, slkChannel)
        else:
            print ("No Slack channels to add! Skipping...")
        
        # Newrelic Dashboard creation stuff
        dash_conds = parm.monitors.get('newrelic')['dashboard']['app_names']
        dash_title = parm.monitors.get('newrelic')['dashboard']['title']
        if not dash_conds:
            print ("No Dashboard conditions specified, skipping...")
        else:
            newrelic.CreateDashboard(dash_conds, dash_title)
 
            