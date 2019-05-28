#!/bin/bash
eval `ssh-agent`
ssh-add ~/.ssh/$3.pem
cd $2
ansible-playbook create-elk.yaml --extra-vars "'product_name=$1'"
ansible-playbook tag-ec2.yaml --extra-vars "'product_name=$1'"
