#!/bin/bash

set -e

if [ "$TRAVIS" != "true" ]; then
    echo "$(basename $0) can only be run by Travis"
    exit 1
fi
if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
    if [ "$TRAVIS_BRANCH" == "master" ]; then
        VERSION="$TRAVIS_TAG"
        if [ -z "$VERSION" ]; then
            VERSION="$TRAVIS_COMMIT"
        fi
        TAG="$DOCKER_REPOSITORY/serverstf:$VERSION"
        docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"
        docker tag serverstf:latest "$TAG"
        docker push "$TAG"
    else
        echo "Not pushing image built from non-master branch"
    fi
else
    echo "Not pushing image built from pull request"
fi
