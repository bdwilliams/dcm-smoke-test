DCM Smoke Test Script
=====================

A Quick Sanity/Smoke-test script for retrieving launch/creation times.

#### Sample

https://gist.github.com/bdwilliams/e3b94fb12b6892cc40f3

#### Install

pip install -r requirements.txt

### Setup

export ES_ACCESS_KEY=YOUR_API_KEY
export ES_SECRET_KEY=YOUR_SECRET_KEY
export ES_ENDPOINT=http://dcm.hostname.com:15000/api/enstratus/2013-12-07
export ES_API_VERSION=2013-12-07

#### Run

./smoke_test.py
