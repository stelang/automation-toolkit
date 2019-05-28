#!/bin/bash
eval `ssh-agent`
ssh-add ~/.ssh/$3.pem
cd $2
ansible-playbook install-metricbeat.yaml --extra-vars "'product_name=$1'"
