import boto3
from copy import deepcopy
from botocore.exceptions import ClientError
import json
import logging
from time import time, sleep

from .constants import taskDefinitionTemplate, containerTemplate, serviceTemplate, networkTemplate, logConfigurationTemplate, dnsConfigTemplate, changesTemplate

class ECS(object):
	
    def __init__(self, parm, profile=None):

        if profile:
            self.session = boto3.session.Session(profile_name=profile)
        else:
            self.session = boto3.session.Session()

        self.product = parm.product
        self.ecs = parm.ecs

        self.ecsClient = self.session.client('ecs')
        self.ec2Client = self.session.client('ec2')
        self.logClient = self.session.client('logs')
        self.r53Client = Route53(self.session)

    def host_all(self):
        """
        Main driver function
        """
        self.currentClusters = self._get_clusters()
        self.vpc = self._get_vpc()
        self.subnets = self._get_subnets()
        self.securityGroups = self._get_security_groups()
        self.logGroups = self._get_log_groups()

        newClusters = self._create_clusters(self.ecs['clusters'])

        containers = self._construct_containers(self.ecs['containers'])

        taskDefinitions, taskDefinitionSecurityGroups = self._construct_task_definitions(containers)
        updatedTaskDefinitions = self._update_task_definitions(taskDefinitions)

        self._create_services(newClusters, updatedTaskDefinitions, taskDefinitionSecurityGroups)

        self.assign_route53()

    def assign_route53(self):
        """
        Based on containers, specifies route 53 entries.
        """
        containers = self.ecs.get('containers')
        if containers:
            containerIps = {c['name']: list() for c in containers}
        else:
            print("There are no containers specified in yaml. Route 53 assignment requires detectable containers.")
            exit()

        tasks = self._get_tasks()

        print("Assigning route 53 entries.")
        for t in tasks:
            for c in t['containers']:
                containerKey = containerIps.get(c['name'])
                if containerKey != None:
                    for n in c['networkInterfaces']:
                        containerKey.append(n['privateIpv4Address'])

        for key, value in containerIps.items():
            if value:
                routeName = self.r53Client.get_r53_name(key)
                self.r53Client.create_route(routeName, value)
                print(f'{routeName} route 53 entry created.')

    def _get_tasks(self):
        """
        Gets current running tasks in clusters.
        """
        tasks = list()

        self._wait_on_task_provision()

        for cluster in self.currentClusters:
            taskArns = self.ecsClient.list_tasks(cluster=cluster)['taskArns']
            tasks += self.ecsClient.describe_tasks(cluster=cluster, tasks=taskArns)['tasks']

        return tasks

    def _wait_on_task_provision(self):
        """
        Waits on tasks to provision themselves before trying to assign route 53 entries.
        """
        services = self.ecs.get('services')

        if not services:
            print("Services must be specified for route53 auto-assign functionality.")
            exit()

        print("Waiting for tasks to provision before assigning route53.")

        clusterServices = {c:list() for c in self.currentClusters}

        for s in services:
            clusterServices[s['cluster']].append(s['serviceName'])

        latestTime = time() + 300*len(clusterServices) # retries for 5 minute * cluster count at max

        for key, value in clusterServices.items():
            while time() < latestTime:
                currentServices = self.ecsClient.describe_services(cluster=key, services=value)['services']
                for cs in currentServices:
                    if cs['desiredCount'] != cs['runningCount']:
                        break
                else:
                    break
                sleep(5)
            else:
                print("Some task was not provisioned")
                exit()

    def _authorize_ports(self, securityGroupId, portMappings):
        """
        Authorizes ports for security group specified.
        """
        securityGroupIngressVars = dict(
                                            GroupId=securityGroupId,
                                            IpPermissions=self._reformat_port_mapping(portMappings)
                                        )

        self.ec2Client.authorize_security_group_ingress(**securityGroupIngressVars)

    def _check_task_definition(self, service, taskDefinitionSecurityGroups):
        """
        If a specific revision task definition is chosen, the current task
        definition is checked to make sure it exists. The security groups necessary
        for the service update is found and added to taskDefinitionSecurityGroups dictionary.
        """
        try:
            taskDefinition = self.ecsClient.describe_task_definition(taskDefinition=service.get('taskDefinition'))['taskDefinition']
        except ClientError:
            print(f"The task definition specified, {service.get('taskDefinition')}, doesn't exist. Please specify another.")
            exit()

        containerSecurityGroups = []
        for container in taskDefinition['containerDefinitions']:

            containerSecurityGroup = self._get_security_group_name(container['name'])
            
            if containerSecurityGroup not in self.securityGroups:
                self._create_security_group(container)

            securityGroupId = self.securityGroups.get(containerSecurityGroup)['GroupId']

            containerSecurityGroups.append(securityGroupId)

        taskDefinitionSecurityGroups[service['taskDefinition']] = containerSecurityGroups

    def _construct_containers(self, containers):
        """
        Takes container specified in yaml and modifies it into the
        appropriate form.
        """
        logging.info('Constructing containers...')
        containerDefinitions = dict()

        for container in containers:
            containerName = container['name']
            portMappings = container.get('portMappings')
            print(portMappings)
            
            if portMappings:
                for pm in portMappings:
                    pm['hostPort'] = pm['containerPort']

            container = {**containerTemplate, **container}

            if not container.get('logConfiguration'):
                container['logConfiguration'] = self._construct_log_configuration(container)

            containerDefinitions[containerName] = container

            securityGroupName = self._get_security_group_name(containerName)

            currentSecurityGroup = self.securityGroups.get(securityGroupName)
            
            if currentSecurityGroup:
                newPorts = self._compare_ports(currentSecurityGroup, portMappings)
                
                if newPorts:
                    logging.info(f'Authorizing new ports for - {securityGroupName}')
                    self._authorize_ports(currentSecurityGroup['GroupId'], newPorts)
            else:
                logging.info(f'Creating security group - {securityGroupName}')
                self._create_security_group(container)

        return containerDefinitions

    def _construct_service(self, service, taskDefinitionSecurityGroups):
        """
        Takes service specified in yaml, and modifies into the appropriate form
        to post to AWS.
        """
        logging.info('Constructing %s service' % service.get('serviceName'))
        service = {**serviceTemplate, **service}

        if not service.get('networkConfiguration'):
            networkConfiguration = self._construct_network_configuration(service, taskDefinitionSecurityGroups)

            service['networkConfiguration'] = networkConfiguration            

        return service

    def _construct_network_configuration(self, service, taskDefinitionSecurityGroups):
        """
        Constructs the network configuration necessary for service.
        """
        networkConfiguration = deepcopy(networkTemplate)

        if self.subnets:
            currentSubnet = self.subnets[0]
            availableIps = currentSubnet['AvailableIpAddressCount']
            if availableIps >= service['desiredCount']:
                subnetId = currentSubnet['SubnetId']
                networkConfiguration['awsvpcConfiguration']['subnets'].append(subnetId)

                currentSubnet['AvailableIpAddressCount'] = availableIps - service['desiredCount']

                self.subnets = sorted(self.subnets, key=lambda s: s['AvailableIpAddressCount'], reverse=True)
            else:
                print("There are not enough free Ips in your VPC")
                exit()
        else:
            print("There are no more available Ip addresses in your VPC")
            exit()

        securityGroups = taskDefinitionSecurityGroups.get(service['taskDefinition'])

        if securityGroups:
            networkConfiguration['awsvpcConfiguration']['securityGroups'] = securityGroups
        else:
            print("The task definition specified doesn't have security groups.")
            exit()

        return networkConfiguration

    def _construct_log_configuration(self, container):
        """
        Creates the log configuration necessary for the container.
        """
        containerName = container['name']
        logConfiguration = deepcopy(logConfigurationTemplate)

        logOptions = logConfiguration['options']

        logGroupName = self._get_log_group_name(containerName)

        logOptions['awslogs-group'] = logGroupName
        logOptions['awslogs-region'] = self.session.region_name

        if logGroupName not in self.logGroups:
            logging.info(f'Creating log group - {logGroupName}')
            self.logClient.create_log_group(logGroupName=logGroupName)

        return logConfiguration

    def _compare_ports(self, currentSecurityGroup, portMappings):
        """
        Checking whether the current security group has the ports open specified in PortMappings
        of container.
        """
        containerPorts = {str(pm['containerPort']):pm['protocol'] for pm in portMappings}
        
        newPorts = []

        for permission in currentSecurityGroup['IpPermissions']:
            testPort = str(permission['FromPort'])
            
            if testPort in containerPorts and permission['IpProtocol'] == containerPorts[testPort]:
                containerPorts.pop(testPort)

            if not containerPorts:
                break

        if containerPorts:
            newPorts = [ dict(containerPort=cp, protocol=cpp) for cp,cpp in containerPorts.items()]

        return newPorts

    def _compare_services(self, service, currentService, updatedTaskDefinitions):
        """
        Compares service currently in aws, versus one specified by yaml.
        """
        currentService = self._sanitize_service(currentService)

        if currentService['taskDefinition'] not in updatedTaskDefinitions and currentService == service:
            return False

        return True

    def _create_services(self, newClusters, updatedTaskDefinitions, taskDefinitionSecurityGroups):
        """
        Creates or updates the services specified in yaml.
        """
        logging.info('Creating services...')
        for service in self.ecs.get('services'):
            if service.get('taskDefinition') not in updatedTaskDefinitions:
                self._check_task_definition(service, taskDefinitionSecurityGroups)

            service = self._construct_service(service, taskDefinitionSecurityGroups)

            if service.get('cluster') in newClusters:
                self.ecsClient.create_service(**service)
            else:
                serviceArns = self.ecsClient.list_services(cluster=service['cluster'])['serviceArns']
                if serviceArns:
                    currentServices = self.ecsClient.describe_services(cluster=service['cluster'], services=serviceArns)['services']
                    currentServices = {cs['serviceName']: cs for cs in currentServices}
                else:
                    currentServices = dict()

                serviceName = service['serviceName']
                if serviceName not in currentServices:
                    self.ecsClient.create_service(**service)
                else:
                    if self._compare_services(service, currentServices[serviceName], updatedTaskDefinitions):
                        popFields = ['cluster', 'service', 'desiredCount', 'taskDefinition', 'deploymentConfiguration', 'networkConfiguration', 'platformVersion', 'forceNewDeployment', 'healthCheckGracePeriodSeconds']
                        service['service'] = serviceName

                        service = {key: value for key, value in service.items() if key in popFields}
                        self.ecsClient.update_service(**service)

    def _get_security_groups(self):
        """
        Gets all security groups, and maps them by GroupName for easy access.
        """
        logging.info('Getting security groups...')
        filters=[dict(Name='vpc-id', Values=[self.vpc])]

        securityGroups = self.ec2Client.describe_security_groups(Filters=filters)['SecurityGroups']

        return {sg['GroupName']:sg for sg in securityGroups}

    def _create_security_group(self, container):
        """
        Creates securityGroup for container
        """
        containerName = container['name']
        portMappings = container.get('portMappings')

        securityGroupName = self._get_security_group_name(containerName)
        securityGroupVars = dict(   
                                    Description=f'Security group for {containerName} container',
                                    GroupName=securityGroupName,
                                    VpcId=self.vpc
                                )

        securityGroupId = self.ec2Client.create_security_group(**securityGroupVars)['GroupId']
        
        newSecurityGroup = self.ec2Client.describe_security_groups(GroupIds=[securityGroupId])['SecurityGroups'][0]
        self.securityGroups[securityGroupName] = newSecurityGroup
        
        self._waiter(self.ec2Client.create_tags, Resources=[securityGroupId], Tags=[dict(Key='Name', Value=securityGroupName)])

        if portMappings:
            self._authorize_ports(securityGroupId, portMappings)

    def _reformat_port_mapping(self, portMappings):
        """
        Passed a set of all portMappings for taskdefinition
        """
        IpPermissions = []
        for pm in portMappings:
            permission = dict(
                                FromPort=int(pm['containerPort']),
                                IpProtocol=pm['protocol'],
                                IpRanges=[dict(CidrIp='0.0.0.0/0')],
                                ToPort=int(pm['containerPort'])
                            )
            IpPermissions.append(permission)

        return IpPermissions

    def _get_vpc(self):
        """
        Gets vpc if not specified in yaml. If there is more than one vpc,
        and none are specified, error out.
        """
        logging.info('Getting vpc...')
        vpcs = self.ec2Client.describe_vpcs()['Vpcs']

        if hasattr(self, 'vpc'):
            for v in vpcs:
                if v['VpcId'] == self.vpc:
                    return self.vpc
            else:
                print(f"VpcId specified, {self.vpc}, doesn't exist in AWS. Please specify another vpc.")
                exit()
        else:
            if len(vpcs) > 1:
                print("There is more than one vpc, please specify vpc in configuration")
                exit()
            elif len(vpcs) == 0:
                print("There are no vpcs available in your boto profile, please create one")
                exit()
            else:
                return vpcs[0]['VpcId']

    def _get_subnets(self):
        """
        Gets subnets of vpc
        """
        logging.info('Getting subnets...')
        filters=[dict(Name='vpc-id', Values=[self.vpc])]

        subnets = self.ec2Client.describe_subnets(Filters=filters)['Subnets']

        return sorted(subnets, key=lambda s: s['AvailableIpAddressCount'], reverse=True)

    def _construct_task_definitions(self, containers):
        """
        Uses task definition template to create the required postable dictionary.
        """
        logging.info('Constructing task definitions...')

        taskDefinitionSecurityGroups = dict()

        taskDefinitions = dict()

        if not self.ecs.get('taskDefinitions'):
            return dict()

        for td in self.ecs.get('taskDefinitions'):
            td['cpu'] = str(td['cpu'])
            td['memory'] = str(td['memory'])

            taskDefinitionFamily = td['family']
            containerDefinitions = []
            taskDefinitionSecurityGroups[taskDefinitionFamily] = []

            for c in td['containers']:
                containerDefinition = containers.get(c)
                if containerDefinition:
                    containerDefinitions.append(containerDefinition)
                    securityGroupName = self._get_security_group_name(c)
                    securityGroupId = self.securityGroups.get(securityGroupName)['GroupId']
                    taskDefinitionSecurityGroups[taskDefinitionFamily].append(securityGroupId)
                else:
                    print(f"The container definition for, {c}, is not specified in the .yaml. Please specify the container, or use another name.")
                    exit()

            td['containerDefinitions'] = containerDefinitions

            td.pop('containers')

            td = {**taskDefinitionTemplate, **td}

            taskDefinitions[td['family']] = td

        return taskDefinitions, taskDefinitionSecurityGroups

    def _update_task_definitions(self, taskDefinitions):
        """
        Updates task definitions that need to be updated.
        """
        logging.info('Updating task definitions...')
        updatedTaskDefinitions = []

        if not taskDefinitions:
            return updatedTaskDefinitions

        for key, value in taskDefinitions.items():
            if self._compare_task_definitions(value):
                logging.info(f'Registering task definition - {key}')
                self.ecsClient.register_task_definition(**value)
                updatedTaskDefinitions.append(key)

        return updatedTaskDefinitions

    def _compare_task_definitions(self, taskDefinition):
        """
        Compares task definition specified vs the latest one in aws.
        """
        updateTaskDefinition = True
        try:
            latestTaskDefinition = self.ecsClient.describe_task_definition(taskDefinition=taskDefinition['family'])['taskDefinition']
            
            latestTaskDefinition = self._sanitize_task_definition(latestTaskDefinition)
            if latestTaskDefinition == taskDefinition:
                updateTaskDefinition = False
        except ClientError:
            pass

        return updateTaskDefinition

    def _create_clusters(self, clusters):
        """
        Creates clusters if they don't exist, or they're deactivated.
        """
        logging.info('Creating new clusters...')
        newClusters = set()
        for cluster in clusters:
            if cluster not in self.currentClusters:
                response = self.ecsClient.create_cluster(clusterName=cluster)['cluster']
                self.currentClusters.append(response['clusterName'])

                newClusters.add(cluster)

        return newClusters
                 
    def _get_clusters(self):
        """
        Checking whether ecs clusters specified exist.
        """
        logging.info('Getting clusters...')
        clusters = [c for c in self.ecs['clusters']]
        
        awsClusters = self.ecsClient.describe_clusters(clusters=clusters)['clusters']

        return [c['clusterName'] for c in awsClusters if c['status'] == 'ACTIVE']

    def _get_service_tasks(self, cluster):
        """
        Get all tasks running via service on cluster.
        This will be used to compare against total task count on cluster,
        if there are tasks not being run by services. Those tasks will be
        denoted, and later wrapped in basic service. Unless specified
        otherwise.

        Returns tuple of services mapped to their task definitions, and
        number of tasks running via services.
        """
        serviceArns = self.ecs_client.list_services(cluster=self._get_name(cluster))['serviceArns']

        waiter = self.ecs_client.get_waiter('services_stable')
        waiter.wait(cluster=cluster, services=serviceArns)

        services = self.ecs_client.describe_services(cluster=cluster, services=serviceArns)['services']

        services_task_count = 0
        service_tasks = dict()

        for service in services:
            services_task_count += service['desiredCount']

            service_tasks[service['serviceArn']] = service['taskDefinition']

        return (service_tasks, services_task_count)

    def _get_name(self, name, delim=None, prefix=False, rf=False):
        """
        Simple helper function for parsing yaml
        """
        if not delim:
            delim = '.'

        if rf:
            index = name.rfind(delim)
        else:
            index = name.find(delim)

        if index == -1:
            return name

        if not prefix:
            return name[index+1:]
        else:
            return name[:index]
    
    def _sanitize_task_definition(self, taskDefinition):
        """
        Takes task definition pulled from aws, and morphs into a form that can be 
        compared to the task definition specified in the yaml.
        """
        taskDefinitionFields = [ 'family', 'taskRoleArn', 'executionRoleArn', 'networkMode', 'containerDefinitions', 'volumes', 'placementConstraints', 'requiresCompatibilities', 'cpu', 'memory' ]

        taskDefinition = {k: taskDefinition.get(k) for k in taskDefinitionFields if taskDefinition.get(k)}

        executionRoleArn = taskDefinition.get('executionRoleArn')

        if executionRoleArn:
            taskDefinition['executionRoleArn'] = self._get_name(executionRoleArn, delim='/')

        taskRoleArn = taskDefinition.get('taskRoleArn')

        if taskRoleArn:
            taskDefinition['taskRoleArn'] = self._get_name(taskRoleArn, delim='/')

        taskDefinition = self._recur_sanitize(taskDefinition, deepcopy(taskDefinition))

        return taskDefinition

    def _recur_sanitize(self, root, copy):
        """
        Recursively removes all empty dictionary elements.
        """
        for key, value in root.items():
            if isinstance(value, dict):
                self._recur_sanitize(value, copy[key])

            if isinstance(value, list):
                for i in range(0, len(value)):
                    if isinstance(value[i], dict):
                        self._recur_sanitize(value[i], copy[key][i])

            if not copy[key]:
                copy.pop(key)

        return copy

    def _sanitize_service(self, service):
        """
        Takes service pulled from aws, and puts in a form that can be compared to
        the service specified in the yaml.
        """
        serviceFields = [ 'clusterArn', 'serviceName', 'taskDefinition', 'loadBalancers', 'serviceRegistries', 'desiredCount', 'clientToken', 'launchType', 'platformVersion', 'role', 'deploymentConfiguration', 'placementConstraints', 'placementStrategy', 'networkConfiguration', 'healthCheckGracePeriodSeconds', 'schedulingStrategy' ]

        service = {k: service.get(k) for k in serviceFields if service.get(k)}

        service['cluster'] = self._get_name(service.pop('clusterArn'), '/')

        taskDefinition = self._get_name(service['taskDefinition'], delim='/')
        taskDefinition = self._get_name(taskDefinition, delim=':', rf=True, prefix=True)
        
        service['taskDefinition'] = self._get_name(taskDefinition)

        return service

    def _pp(self, string):
        """
        Helps with debugging.
        """
        return json.dumps(string, sort_keys=True, indent=4)

    def _get_security_group_name(self, containerName):
        return f'ecs-{containerName}-sg'

    def _get_log_group_name(self, containerName):
        return f'/ecs/container/{containerName}'

    def _create_log_groups(self, updatedTaskDefinitions):
        """
        Creates the necessary log groups for containers 
        """
        logClient = self.session.client('logs')

        logGroups = logClient.describe_log_groups(logGroupNamePrefix='/ecs')['logGroups']

        for key in updatedTaskDefinitions.keys():
            logGroupName = f'/ecs/{key}'

            if logGroupName not in {lg['logGroupName'] for lg in logGroups}:
                logClient.create_log_group(logGroupName=logGroupName)

    def _get_log_groups(self):
        """
        Gets log groups from aws
        """
        logging.info('Getting log groups...')
        logGroups = self.logClient.describe_log_groups(logGroupNamePrefix='/ecs')['logGroups']

        return [lg['logGroupName'] for lg in logGroups]

    def _waiter(self, fn, retry_period=10, **kwargs):
        """
        When adding a security group, the function returns, but
        then tags can't be added to it. There's a delay between the
        add, and when the security group is accessible. Generalized
        the wait function, incase this sort of use case appears elsewhere. 

        It just retries the command for the given retry_period.
        """
        retryEnd = retry_period + time()
        flag = True
        
        while flag and time() < retryEnd:
            try:
                fn(**kwargs)
                flag = False
            except ClientError:
                pass

        return flag

class Route53(object):

    def __init__(self, session, hostedZoneId=None):

        self.client = session.client('route53')
        self.hostedZoneId, self.hostedZoneName = self._get_hosted_zone()

    def _get_hosted_zone(self, zoneId=None):     
        hostedZones = self.client.list_hosted_zones()['HostedZones']

        if zoneId:
            for hz in hostedZones:
                if zoneId == hz['Id']:
                    return zoneId, hz['Name']
            else:
                print("Hosted Zone Id specified doesn't exist.")
                exit()

        if len(hostedZones) > 1:
            print("More than one hosted zone, and only one is specified.")
            exit()
        elif len(hostedZones) == 0:
            print("There are no hosted zones in your vpc, please create one.")
            exit()
        else:
            return hostedZones[0]['Id'], hostedZones[0]['Name']

    def get_routes(self):
        resourceRecordSets = self.client.list_resource_record_sets(HostedZoneId=self.hostedZoneId)['ResourceRecordSets']

        return {rrs['Name']: rrs for rrs in resourceRecordSets}

    def create_route(self, routeName, ips):
        resourceRecord = dict(  HostedZoneId=self.hostedZoneId,
                                ChangeBatch=dict())

        changes = deepcopy(changesTemplate)

        resourceRecordSet = changes['ResourceRecordSet']
        resourceRecordSet['Name'] = routeName

        for ip in ips:
            resourceRecordSet['ResourceRecords'].append(dict(Value=ip))
        
        resourceRecord['ChangeBatch']['Changes'] = [changes]

        self.client.change_resource_record_sets(**resourceRecord)

    def get_r53_name(self, containerName):
        import re

        containerNameCopy = re.sub(r'[^a-zA-Z0-9\-]', '', containerName)

        return f'{containerNameCopy}.ecs.{self.hostedZoneName}'

    def compare_route(self, routeName, ips):
        currentRoute = self.routes.get(routeName)

        currentRouteDNS = {resource.get('Value') for resource in currentRoute['ResourceRecords']}

        ips = list(set(currentRouteDNS + ips))

        return ips
