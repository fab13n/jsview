#!/bin/bash

set -e

VERSION=$1

cd $(dirname $0)

# Check if version has been provided
if [[ "$VERSION" == "" ]]; then
    CURRENT_VERSION=$(cat jsonschema_cn/__init__.py | grep '^\s*__version__\s*=' | cut -d'"' -f2)
    echo "Usage: $0 <new_version number>. Current version is $CURRENT_VERSION."
    if git tag | grep -q "^v$CURRENT_VERSION$"; then
        echo "This version has already been tagged."
    else
        echo "This version has not been tagged yet."
    fi
    exit 1
fi

if [[ ! -f .credentials ]]; then
    echo "Missing a .credentials file with LOGIN=xxx and PASSWORD=xxx lines"
    exit 2
fi

# Change version in sources
sed -i "s/^__version__\\s*=.*/__version__ = \"$VERSION\"/" jsonschema_cn/__init__.py

# Commit + tag + push change(s)
if [[ $(git status -s) != "" ]]; then
    echo "Uncommitted files, please commit and try again"
    exit 3
    # git commit -am "Published version $VERSION"
fi
git tag -a "v$VERSION" -m "Published version $VERSION"
git push

# Rebuild
python3 setup.py sdist bdist_wheel || exit 1

# Publish
. .credentials
twine upload \
      --username "$LOGIN" \
      --password "$PASSWORD" \
      --repository-url https://upload.pypi.org/legacy/ \
      dist/*-$VERSION.*
