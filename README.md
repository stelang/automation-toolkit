### PARM - Pipeline, Alerts, Recovery and Monitor creator v0.0.12

<p align="center">
  <img src="https://www.seriouseats.com/images/2014/09/20140923-chicken-parm-recipe-38.jpg" width="350"/>
</p>

### Description
    PARM is a light weight python module that creates dashboards, alerts and pipeline Jenkinsfile automagically
    All the developer has to do is push a parm.yaml file in thier repo at root level
    A jenkins job will pick up the parm.yaml and create dashboards, alerts and pieplines automatically

    PARM v0.0.12
    Functionality:
    1. Creates metricbeat dashboards automatically for tagged AWS resources.
       tagging norm: Product: <product_name>
       this name should match the name in parm.yaml
       see example below
    

### create virtualenv

    $ virtualenv -p python3 venv
    $ source venv/bin/activate

### Running the main() (you may create some awesome dashboards on the fly by runnings the commands below)
    cd cm-devops-parm
    (venv)$ python3 setup.py install
    (venv)$ parm init
    (venv)$ parm create-dashboards parm/parm.yaml
    (venv)$ parm host parm/parm.yaml
    
### TODO
