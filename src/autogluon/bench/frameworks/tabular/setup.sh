#!/bin/bash

set -eo pipefail

GIT_URI=$1  # AMLB Git URI
BRANCH=$2  # AMLB branch
DIR=$3  # from root of benchmark run
AMLB_FRAMEWORK=$4  # e.g. AutoGluon_dev:test
AMLB_USER_DIR=$5  # directory where AMLB customizations are located


if [ ! -d $DIR ]; then
  mkdir -p $DIR
fi

echo "Cloning $GIT_URI#$BRANCH..."
repo_name=$(basename -s .git $(echo $GIT_URI))
git clone --depth 1 --single-branch --branch ${BRANCH} --recurse-submodules ${GIT_URI} $DIR/$repo_name

# create virtual env
python3 -m venv $DIR/.venv
source $DIR/.venv/bin/activate

# install latest AMLB
pip install --upgrade pip
pip install --upgrade setuptools wheel
git clone --depth 1 --branch stable https://github.com/openml/automlbenchmark.git $DIR/automlbenchmark
pip install -r $DIR/automlbenchmark/requirements.txt
