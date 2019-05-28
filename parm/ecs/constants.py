taskDefinitionTemplate = {
                'taskRoleArn': 'ecsTaskExecutionRole',
                'executionRoleArn': 'ecsTaskExecutionRole',
                'networkMode': 'awsvpc',
                'requiresCompatibilities': ['FARGATE'],
                'cpu': '512',
                'memory': '1GB'
}

containerTemplate = {
                        'essential': True
                    }

logConfigurationTemplate = {    
                                'logDriver': 'awslogs',
                                'options':  {
                                                'awslogs-group': '',
                                                'awslogs-region': 'us-east-1',
                                                'awslogs-stream-prefix': 'ecs'
                                            }
                            }

serviceTemplate =   {
                        'desiredCount': 1,
                        'launchType': 'FARGATE',
                        'platformVersion': 'LATEST',
                        'deploymentConfiguration':  {
                                                        'maximumPercent': 200,
                                                        'minimumHealthyPercent': 50
                                                    }
}

dnsConfigTemplate = {
                        "RoutingPolicy": 'MULTIVALUE',
                        "DnsRecords":[
                            {
                                'Type': 'A',
                                'TTL': 60
                            }
                        ]
                    }

networkTemplate =  {
                        'awsvpcConfiguration':  {
                                                    'subnets': [],
                                                    'securityGroups': [],
                                                    'assignPublicIp': 'ENABLED'
                                                }
                    }

changesTemplate = {
    'Action': 'UPSERT',
    'ResourceRecordSet': {
        'Type': 'A',
        'TTL': 300,
        'ResourceRecords': []
    }
}