#!/bin/sh

cd /data/git-mirrors/github.com/$1/$2.git

git remote update
git update-server-info

