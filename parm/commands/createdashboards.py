""" The CreateDashboards command."""
from .base import Base

from parm import Parm
from parm.utilities import TemplateHandler, write_file, get_conf_file, get_parm_file
from parm.collectors import Metricbeat
from parm.collectors import Costexplorer
import requests, datetime, json, itertools

class CreateDashboards(Base):
    """Creates dashboards based on parm.yaml"""
    # TODO move payloads to constants or jinja2, create elastic object with functions for
    def run(self):
        parm = Parm(get_parm_file(self.options.get('<file>')))
        print(parm.collectors.get('metricbeat'))
        if not (parm.collectors.get('metricbeat')):
            print('metricbeat disabled, skipping')
        else:
            th = TemplateHandler(parm)
            ansible = th.get_rendered_templates('ansible')
            write_file(get_conf_file('../../ansible/group_vars/all.yaml'), ansible[0])
            mb = th.get_rendered_templates('metricbeat')
            write_file(get_conf_file('../../output/metricbeat.yml'), mb[0])
            metricbeat = Metricbeat(parm)
            responseCode = metricbeat.createMetricbeatIndex()
            if responseCode != 0:
                print("Ansible failed for metricbeat, exiting")
                #exit()

        # check for cost explorer conditions
        if not (parm.collectors.get('costexplorer')['howfarback']):
            print('Costexplorer disabled, skipping')
        elif not (parm.aws.get('account_id')):
            print('AWS account id missing in parm.yaml, cost dashboard creation failed, exiting')
            exit()
        else:
            i = 0
            j = 1
            linkedAccount = parm.aws.get('account_id')
            costexplorer = Costexplorer(parm, parm.aws.get('boto_profile'))
            # fetch cost data for specified time in days using howfarback variable
            for _ in itertools.repeat(None, parm.collectors.get('costexplorer')['howfarback']):               
                costDict = costexplorer.get_cost_and_usage(linkedAccount, i, j)
                url = "http://%s-elk.%s:9200/costexplorer-%s.%s" % (parm.get_property('boto_profile', nested='aws'),parm.get_property('zone', nested='aws'),parm.product,((datetime.datetime.today() - datetime.timedelta(int(i)))).strftime('%Y-%m-%d'))
                headerz = {'Content-Type': "application/json"}
                payload = {
                        "mappings": {
                            "_doc": {
                            "properties": {
                                "@timestamp": {
                                "type": "date",
                                "format": "yyyy-MM-dd HH:mm:ss"
                                },
                                "AWS CloudTrail": {
                                "type": "float"                    
                                },
                                "AWS Cost Explorer": {
                                "type": "float"                      
                                },
                                "AWS Direct Connect": {
                                "type": "float"                      
                                },
                                "AWS Key Management Service": {
                                "type": "float"                      
                                },
                                "AWS Lambda": {
                                "type": "float"                      
                                },
                                "Amazon DynamoDB": {
                                "type": "float"                      
                                },
                                "Amazon EC2 Container Registry (ECR)": {
                                "type": "float"                      
                                },
                                "Amazon Elastic Compute Cloud - Compute": {
                                "type": "float"                      
                                },
                                "Amazon Elastic File System": {
                                "type": "float"                      
                                },
                                "Amazon Elastic Load Balancing": {
                                "type": "float"                      
                                },
                                "Amazon Relational Database Service": {
                                "type": "float"                      
                                },
                                "Amazon Route 53": {
                                "type": "float"                      
                                },
                                "Amazon Simple Email Service": {
                                "type": "float"                      
                                },
                                "Amazon Simple Notification Service": {
                                "type": "float"                      
                                },
                                "Amazon Simple Queue Service": {
                                "type": "float"                      
                                },
                                "Amazon Simple Storage Service": {
                                "type": "float"                      
                                },
                                "AmazonCloudWatch": {
                                "type": "float"                      
                                },
                                "EC2 - Other": {
                                "type": "float"                      
                                }
                            }
                        }
                    }
                }
                payload = json.dumps(payload)
                response = requests.put(url, data=payload, headers=headerz)
                print(response.text)
                
               

                # post to ES daily data
                url = "http://%s-elk.%s:9200/costexplorer-%s.%s/_doc/1" % (parm.get_property('boto_profile', nested='aws'),parm.get_property('zone', nested='aws'),parm.product,((datetime.datetime.today() - datetime.timedelta(int(i)))).strftime('%Y-%m-%d'))
                headerz = {'Content-Type': "application/json"}
                response = requests.put(url, data=json.dumps(costDict), headers=headerz)
                print(response.text)
                i = i + 1
                j = j + 1

            # create index pattern saved object
            url = "http://%s-elk.%s:5601/api/saved_objects/index-pattern/costexplorer-%s" % (parm.get_property('boto_profile', nested='aws'),parm.get_property('zone', nested='aws'), parm.product)
            headerz = {'Content-Type': "application/json", 'kbn-xsrf': "true"}
            payload = {
                "attributes": {
                    "title": "costexplorer-%s*" % parm.product,
                    "timeFieldName": "@timestamp"
                }
            }
            response = requests.post(url, data=json.dumps(payload), headers=headerz)
            print(response.text)

            # create viz monthly saved object
            payload = {
                "attributes": {
                    "title": "costViz",
                    "visState": "{\"aggs\":[{\"enabled\":true,\"id\":\"2\",\"params\":{\"customLabel\":\"EC2 Cost in $USD\",\"field\":\"Amazon Elastic Compute Cloud - Compute\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"4\",\"params\":{\"customLabel\":\"EFS Cost in $USD\",\"field\":\"Amazon Elastic File System\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"1\",\"params\":{\"customLabel\":\"Dynamo DB Cost in $USD\",\"field\":\"Amazon DynamoDB\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"3\",\"params\":{\"customLabel\":\"ECR Cost in $USD\",\"field\":\"Amazon EC2 Container Registry (ECR)\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"5\",\"params\":{\"customLabel\":\"ELB Cost in $USD\",\"field\":\"Amazon Elastic Load Balancing\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"6\",\"params\":{\"customLabel\":\"RDS Cost in $USD\",\"field\":\"Amazon Relational Database Service\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"7\",\"params\":{\"customLabel\":\"Route 53 Cost in $USD\",\"field\":\"Amazon Route 53\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"8\",\"params\":{\"customLabel\":\"SES Cost in $USD\",\"field\":\"Amazon Simple Email Service\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"9\",\"params\":{\"customLabel\":\"SNS Cost in $USD\",\"field\":\"Amazon Simple Notification Service\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"10\",\"params\":{\"customLabel\":\"SQS Cost in $USD\",\"field\":\"Amazon Simple Queue Service\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"11\",\"params\":{\"customLabel\":\"S3 Cost in $USD\",\"field\":\"Amazon Simple Storage Service\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"12\",\"params\":{\"customLabel\":\"Cloud Watch Cost in $USD\",\"field\":\"AmazonCloudWatch\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"13\",\"params\":{\"customLabel\":\"Cloud Trail Cost in $USD\",\"field\":\"AWS CloudTrail\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"14\",\"params\":{\"customLabel\":\"Cost Explorer Cost in $USD\",\"field\":\"AWS Cost Explorer\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"15\",\"params\":{\"customLabel\":\"Direct Connect Cost in $USD\",\"field\":\"AWS Direct Connect\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"16\",\"params\":{\"customLabel\":\"KMS Cost in $USD\",\"field\":\"AWS Key Management Service\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"17\",\"params\":{\"customLabel\":\"Lambda Cost in $USD\",\"field\":\"AWS Lambda\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"18\",\"params\":{\"customLabel\":\"EC2 (Other) Cost in $USD\",\"field\":\"EC2 - Other\"},\"schema\":\"metric\",\"type\":\"sum\"},{\"enabled\":true,\"id\":\"19\",\"params\":{\"customInterval\":\"2h\",\"customLabel\":\"Month\",\"extended_bounds\":{},\"field\":\"@timestamp\",\"interval\":\"M\",\"min_doc_count\":0},\"schema\":\"bucket\",\"type\":\"date_histogram\"}],\"params\":{\"perPage\":7,\"showMeticsAtAllLevels\":false,\"showPartialRows\":false,\"showTotal\":true,\"sort\":{\"columnIndex\":null,\"direction\":null},\"totalFunc\":\"sum\"},\"title\":\"costViz\",\"type\":\"table\"}",
                    "uiStateJSON": "{\"vis\":{\"params\":{\"sort\":{\"columnIndex\":null,\"direction\":null}}}}",
                    "description": "",
                    "version": 1,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{\"index\":\"costexplorer-%s\",\"filter\":[],\"query\":{\"language\":\"lucene\",\"query\":\"\"}}" % parm.product
                    }
                }
            }
            url = "http://%s-elk.%s:5601/api/saved_objects/visualization/costViz" % (parm.get_property('boto_profile', nested='aws'),parm.get_property('zone', nested='aws'))
            headerz = {'Content-Type': "application/json", 'kbn-xsrf': "true"}
            response = requests.post(url, data=json.dumps(payload), headers=headerz)
            print(response.text)

            # create viz daily saved object
            payload = {
                "attributes": {
                    "title": "costVizDays",
                    "visState": "{\"title\":\"costVizDays\",\"type\":\"table\",\"params\":{\"perPage\":30,\"showMeticsAtAllLevels\":false,\"showPartialRows\":false,\"showTotal\":true,\"sort\":{\"columnIndex\":null,\"direction\":null},\"totalFunc\":\"sum\"},\"aggs\":[{\"id\":\"2\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Elastic Compute Cloud - Compute\",\"customLabel\":\"EC2 Cost in $USD\"}},{\"id\":\"4\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Elastic File System\",\"customLabel\":\"EFS Cost in $USD\"}},{\"id\":\"1\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon DynamoDB\",\"customLabel\":\"Dynamo DB Cost in $USD\"}},{\"id\":\"3\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon EC2 Container Registry (ECR)\",\"customLabel\":\"ECR Cost in $USD\"}},{\"id\":\"5\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Elastic Load Balancing\",\"customLabel\":\"ELB Cost in $USD\"}},{\"id\":\"6\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Relational Database Service\",\"customLabel\":\"RDS Cost in $USD\"}},{\"id\":\"7\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Route 53\",\"customLabel\":\"Route 53 Cost in $USD\"}},{\"id\":\"8\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Simple Email Service\",\"customLabel\":\"SES Cost in $USD\"}},{\"id\":\"9\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Simple Notification Service\",\"customLabel\":\"SNS Cost in $USD\"}},{\"id\":\"10\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Simple Queue Service\",\"customLabel\":\"SQS Cost in $USD\"}},{\"id\":\"11\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Simple Storage Service\",\"customLabel\":\"S3 Cost in $USD\"}},{\"id\":\"12\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AmazonCloudWatch\",\"customLabel\":\"Cloud Watch Cost in $USD\"}},{\"id\":\"13\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AWS CloudTrail\",\"customLabel\":\"Cloud Trail Cost in $USD\"}},{\"id\":\"14\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AWS Cost Explorer\",\"customLabel\":\"Cost Explorer Cost in $USD\"}},{\"id\":\"15\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AWS Direct Connect\",\"customLabel\":\"Direct Connect Cost in $USD\"}},{\"id\":\"16\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AWS Key Management Service\",\"customLabel\":\"KMS Cost in $USD\"}},{\"id\":\"17\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AWS Lambda\",\"customLabel\":\"Lambda Cost in $USD\"}},{\"id\":\"18\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"EC2 - Other\",\"customLabel\":\"EC2 (Other) Cost in $USD\"}},{\"id\":\"19\",\"enabled\":true,\"type\":\"date_histogram\",\"schema\":\"bucket\",\"params\":{\"field\":\"@timestamp\",\"interval\":\"d\",\"customInterval\":\"2h\",\"min_doc_count\":0,\"extended_bounds\":{},\"customLabel\":\"Day\"}}]}",
                    "uiStateJSON": "{\"vis\":{\"params\":{\"sort\":{\"columnIndex\":null,\"direction\":null}}}}",
                    "description": "",
                    "version": 1,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{\"index\":\"costexplorer-%s\",\"filter\":[],\"query\":{\"language\":\"lucene\",\"query\":\"\"}}" % parm.product
                    }
                }
            }
            url = "http://%s-elk.%s:5601/api/saved_objects/visualization/costVizDays" % (parm.get_property('boto_profile', nested='aws'),parm.get_property('zone', nested='aws'))
            headerz = {'Content-Type': "application/json", 'kbn-xsrf': "true"}
            response = requests.post(url, data=json.dumps(payload), headers=headerz)
            print(response.text)
            
            # create viz title monthly saved object
            payload = {
                "attributes": {
                    "title": "Cost Title Monthly",
                    "visState": "{\"title\":\"Cost Title Monthly\",\"type\":\"markdown\",\"params\":{\"fontSize\":18,\"markdown\":\"## Monthly Cost per service in $USD\"},\"aggs\":[]}",
                    "uiStateJSON": "{}",
                    "description": "",
                    "version": 1,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{}"
                    }
                }
            }
            url = "http://%s-elk.%s:5601/api/saved_objects/visualization/costTitleMonths" % (parm.get_property('boto_profile', nested='aws'),parm.get_property('zone', nested='aws'))
            headerz = {'Content-Type': "application/json", 'kbn-xsrf': "true"}
            response = requests.post(url, data=json.dumps(payload), headers=headerz)
            print(response.text)

            # create viz title daily saved object
            payload = {
                "attributes": {
                    "title": "Cost Title Daily",
                    "visState": "{\"title\":\"Cost Title Daily\",\"type\":\"markdown\",\"params\":{\"fontSize\":18,\"markdown\":\"## Daily Cost per service in $USD\"},\"aggs\":[]}",
                    "uiStateJSON": "{}",
                    "description": "",
                    "version": 1,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{}"
                    }
                }
            }
            url = "http://%s-elk.%s:5601/api/saved_objects/visualization/costTitleDays" % (parm.get_property('boto_profile', nested='aws'),parm.get_property('zone', nested='aws'))
            headerz = {'Content-Type': "application/json", 'kbn-xsrf': "true"}
            response = requests.post(url, data=json.dumps(payload), headers=headerz)
            print(response.text)

            # create viz bar chart monthly saved object
            payload = {
                "attributes": {
                    "title": "Cost Bar Chart Monthly",
                    "visState": "{\"title\":\"Cost Bar Chart Monthly\",\"type\":\"histogram\",\"params\":{\"type\":\"histogram\",\"grid\":{\"categoryLines\":false,\"style\":{\"color\":\"#eee\"}},\"categoryAxes\":[{\"id\":\"CategoryAxis-1\",\"type\":\"category\",\"position\":\"bottom\",\"show\":true,\"style\":{},\"scale\":{\"type\":\"linear\"},\"labels\":{\"show\":true,\"truncate\":100,\"filter\":false,\"rotate\":75},\"title\":{}}],\"valueAxes\":[{\"id\":\"ValueAxis-1\",\"name\":\"LeftAxis-1\",\"type\":\"value\",\"position\":\"left\",\"show\":true,\"style\":{},\"scale\":{\"type\":\"linear\",\"mode\":\"normal\"},\"labels\":{\"show\":true,\"rotate\":0,\"filter\":false,\"truncate\":100},\"title\":{\"text\":\"Cost in $USD\"}}],\"seriesParams\":[{\"show\":\"true\",\"type\":\"histogram\",\"mode\":\"stacked\",\"data\":{\"label\":\"Dynamo DB\",\"id\":\"1\"},\"valueAxis\":\"ValueAxis-1\",\"drawLinesBetweenPoints\":true,\"showCircles\":true},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"3\",\"label\":\"ECR\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"4\",\"label\":\"EC2\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"5\",\"label\":\"EFS\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"6\",\"label\":\"ELB\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"7\",\"label\":\"RDS\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"8\",\"label\":\"Route 53\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"9\",\"label\":\"SES\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"10\",\"label\":\"SNS\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"11\",\"label\":\"SQS\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"12\",\"label\":\"S3\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"13\",\"label\":\"Cloudwatch\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"14\",\"label\":\"Cloudtrail\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"15\",\"label\":\"Cost Explorer\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"16\",\"label\":\"Direct Connect\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"17\",\"label\":\"KMS\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"18\",\"label\":\"Lambda\"},\"valueAxis\":\"ValueAxis-1\"},{\"show\":true,\"mode\":\"stacked\",\"type\":\"histogram\",\"drawLinesBetweenPoints\":true,\"showCircles\":true,\"data\":{\"id\":\"19\",\"label\":\"EC2-Other\"},\"valueAxis\":\"ValueAxis-1\"}],\"addTooltip\":true,\"addLegend\":true,\"legendPosition\":\"right\",\"times\":[],\"addTimeMarker\":false},\"aggs\":[{\"id\":\"1\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon DynamoDB\",\"customLabel\":\"Dynamo DB\"}},{\"id\":\"2\",\"enabled\":true,\"type\":\"date_histogram\",\"schema\":\"segment\",\"params\":{\"field\":\"@timestamp\",\"interval\":\"M\",\"customInterval\":\"2h\",\"min_doc_count\":1,\"extended_bounds\":{},\"customLabel\":\"Months\"}},{\"id\":\"3\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon EC2 Container Registry (ECR)\",\"customLabel\":\"ECR\"}},{\"id\":\"4\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Elastic Compute Cloud - Compute\",\"customLabel\":\"EC2\"}},{\"id\":\"5\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Elastic File System\",\"customLabel\":\"EFS\"}},{\"id\":\"6\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Elastic Load Balancing\",\"customLabel\":\"ELB\"}},{\"id\":\"7\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Relational Database Service\",\"customLabel\":\"RDS\"}},{\"id\":\"8\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Route 53\",\"customLabel\":\"Route 53\"}},{\"id\":\"9\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Simple Email Service\",\"customLabel\":\"SES\"}},{\"id\":\"10\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Simple Notification Service\",\"customLabel\":\"SNS\"}},{\"id\":\"11\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Simple Queue Service\",\"customLabel\":\"SQS\"}},{\"id\":\"12\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"Amazon Simple Storage Service\",\"customLabel\":\"S3\"}},{\"id\":\"13\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AmazonCloudWatch\",\"customLabel\":\"Cloudwatch\"}},{\"id\":\"14\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AWS CloudTrail\",\"customLabel\":\"Cloudtrail\"}},{\"id\":\"15\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AWS Cost Explorer\",\"customLabel\":\"Cost Explorer\"}},{\"id\":\"16\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AWS Direct Connect\",\"customLabel\":\"Direct Connect\"}},{\"id\":\"17\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AWS Key Management Service\",\"customLabel\":\"KMS\"}},{\"id\":\"18\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"AWS Lambda\",\"customLabel\":\"Lambda\"}},{\"id\":\"19\",\"enabled\":true,\"type\":\"sum\",\"schema\":\"metric\",\"params\":{\"field\":\"EC2 - Other\",\"customLabel\":\"EC2-Other\"}}]}",
                    "uiStateJSON": "{}",
                    "description": "",
                    "version": 1,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{\"index\":\"costexplorer-%s\",\"filter\":[],\"query\":{\"query\":\"\",\"language\":\"lucene\"}}" % parm.product
                    }
                }
            }
            url = "http://%s-elk.%s:5601/api/saved_objects/visualization/costBarMonths" % (parm.get_property('boto_profile', nested='aws'),parm.get_property('zone', nested='aws'))
            headerz = {'Content-Type': "application/json", 'kbn-xsrf': "true"}
            response = requests.post(url, data=json.dumps(payload), headers=headerz)
            print(response.text)

            # create dash saved object
            payload = {
                "attributes": {
                    "title": "%s Cost Dashboard for %s" % (parm.product.capitalize(),parm.get_property('vpc', nested='aws')),
                    "hits": 0,
                    "description": "%s Cost Dashboard for %s (Account: %s)" % (parm.product.capitalize(),parm.get_property('vpc', nested='aws'),parm.get_property('account_id', nested='aws')),
                    "panelsJSON": "[{\"panelIndex\":\"1\",\"gridData\":{\"x\":0,\"y\":9,\"w\":10,\"h\":6,\"i\":\"1\"},\"embeddableConfig\":{\"vis\":{\"params\":{\"sort\":{\"columnIndex\":0,\"direction\":\"desc\"}}}},\"id\":\"costViz\",\"type\":\"visualization\",\"version\":\"6.2.4\"},{\"panelIndex\":\"2\",\"gridData\":{\"x\":0,\"y\":0,\"w\":6,\"h\":2,\"i\":\"2\"},\"id\":\"costTitleMonths\",\"type\":\"visualization\",\"version\":\"6.2.4\"},{\"panelIndex\":\"3\",\"gridData\":{\"x\":0,\"y\":17,\"w\":12,\"h\":17,\"i\":\"3\"},\"embeddableConfig\":{\"vis\":{\"params\":{\"sort\":{\"columnIndex\":0,\"direction\":\"desc\"}}}},\"id\":\"costVizDays\",\"type\":\"visualization\",\"version\":\"6.2.4\"},{\"panelIndex\":\"4\",\"gridData\":{\"x\":0,\"y\":15,\"w\":5,\"h\":2,\"i\":\"4\"},\"id\":\"costTitleDays\",\"type\":\"visualization\",\"version\":\"6.2.4\"},{\"panelIndex\":\"5\",\"gridData\":{\"x\":0,\"y\":2,\"w\":10,\"h\":7,\"i\":\"5\"},\"version\":\"6.2.4\",\"type\":\"visualization\",\"id\":\"costBarMonths\"}]",
                    "optionsJSON": "{\"darkTheme\":false,\"hidePanelTitles\":false,\"useMargins\":true}",
                    "version": 1,
                    "timeRestore": "false",
                    "timeTo": "now",
                    "timeFrom": "now-6M",
                    "refreshInterval": {
                        "display": "Off",
                        "pause": "false",
                        "value": 0
                    },
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{\"query\":{\"language\":\"lucene\",\"query\":\"\"},\"filter\":[],\"highlightAll\":true,\"version\":true}"
                    }
                }
            }
            url = "http://%s-elk.%s:5601/api/saved_objects/dashboard/costDash" % (parm.get_property('boto_profile', nested='aws'),parm.get_property('zone', nested='aws'))
            headerz = {'Content-Type': "application/json", 'kbn-xsrf': "true"}
            response = requests.post(url, data=json.dumps(payload), headers=headerz)
            print(response.text)
