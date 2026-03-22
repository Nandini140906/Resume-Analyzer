#!/bin/bash
set -e
pip install --upgrade pip setuptools wheel
pip install --only-binary=:all: pandas==1.5.3 numpy==1.24.3
pip install -r requirements.txt --no-deps --ignore-installed pandas numpy
pip install -r requirements.txt