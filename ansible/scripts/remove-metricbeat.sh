#!/bin/bash
eval `ssh-agent`
ssh-add ~/.ssh/$3.pem
cd $2
ansible-playbook remove-metricbeat.yaml --extra-vars "'product_name=$1'"
ansible-playbook untag-ec2.yaml --extra-vars "'product_name=$1'"
