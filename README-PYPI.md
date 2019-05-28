PARM - Pipeline, Alerts, Recovery and Monitor creator v0.0.12


Description
This was built by Sid Telang
PARM is a light weight python module that creates dashboards, alerts and pipeline Jenkinsfile automagically
All the developer has to do is push a parm.yaml file in thier repo at root level
A jenkins job will pick up the parm.yaml and create dashboards, alerts and pieplines automatically

PARM v0.0.12
Functionality:
1. Creates metricbeat dashboards automatically for tagged AWS resources.
    tagging norm: Product: <product_name>
    this name should match the name in parm.yaml
    see example below
    
parm.yaml
----------------------------------------------------
Product level values

product: myapp
environment: dev

Kibana Configuration
kibana:
endpoint: <kibana-endpoint>

----------------------------------------------------
    
Getting Started
    
$ virtualenv -p python3 venv
$ cd venv
$ source venv/bin/activate

Running the main() (you may create some awesome dashboards on the fly by runnings the commands below)
(venv)$ pip install parmapp
(venv)$ parm create-dashboards <path-to-your-parm.yaml>
or 
(venv)$ parm cleanup <path-to-your-parm.yaml>