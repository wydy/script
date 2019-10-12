#!/bin/bash

[ ! -d ./report ] && mkdir ./report
[ ! -d ./facts ] && mkdir ./facts
rm -rf ./facts

ansible all -m setup --tree ./facts

python3 ansible.py
