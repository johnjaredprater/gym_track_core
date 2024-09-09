#!/bin/bash

NEW_TAG=$1
K8S_DEPLOYMENT_FILE=deploy/manifests/deployment.yaml

# Replace the old image tag with the new tag
sed -i "s|image: johnjaredprater/gym_track_core:.*|image: johnjaredprater/gym_track_core:$NEW_TAG|g" $K8S_DEPLOYMENT_FILE

# Identify the bot making the change
git config user.name github-actions
git config user.email github-actions@github.com

# Commit the changes
git add $K8S_DEPLOYMENT_FILE
git commit -m "chore: update kubernetes deployment to use docker image tag $NEW_TAG"
git push https://github-actions:${GITHUB_TOKEN}@github.com/johnjaredprater/gym_track_core.git main
