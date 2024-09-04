#!/bin/bash
set -e

pip install -r requirements.txt
cd .venv/lib/python3.9/site-packages
zip -r ../../../../lambda.zip .
cd ../../../../
zip -g lambda.zip *.py
