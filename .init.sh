#! /bin/bash
export PIP_USER=false
npm i -g serverless
cd aws-python-totalgiving-api
sls plugin install -n serverless-python-requirements
sls plugin install -n serverless-lift
sls login
cd stacks
sls deploy -v
cd ../
sls deploy -v
