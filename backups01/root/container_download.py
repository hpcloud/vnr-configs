#!/usr/local/bin/python2.7 -tt
# vim: set ts=4 sw=4 tw=79 et :

from datetime import date, timedelta
import boto3
import botocore
import os
import subprocess


# Global Variables
debug = True
backup_directory = '/data/containers'
containers = ['patches.stackato.com']
today = date.today()
client = ''


# Make a connection to AWS.
def make_connection():
    global client
    client = boto3.client('s3')
    return;


# Create directory
# This creates the full directory structure for:
# backup_directory
# a subdirectory labeled today's date
# a further subdirectory with the container name
def create_directory(container):
    if debug: print "Creating directory: %s/%s/%s" % (backup_directory,
                                                      today.isoformat(),
                                                      container)
    directory = "%s/%s/%s" % (backup_directory, today.isoformat(), container)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return;


# Get the container contents
# This downloads the contents of the specified container into
# <backup_directory>/<today>/<container>
def get_container(container):
    directory = "%s/%s/%s" % (backup_directory, today.isoformat(), container)
    if debug: print "get_container: %s" % directory
    try:
        bucket = client.list_objects(Bucket=container)
    except botocore.exceptions.ClientError, e:
        print e
        print "%s bucket does not exist!" % (container)
        return;
    for key in bucket['Contents']:
        if debug: print key['Key']
        # Check for directories and create as necessary
        subdirs = key['Key'].split('/')
        if len(subdirs) > 1:
            create_directory("%s/%s" % (container, '/'.join(subdirs[:-1])))
        # Download the contents
        file_location = "%s/%s" % (directory, key['Key'])
        if debug: print file_location
        client.download_file(container, key['Key'], file_location)
    return;


# Rotate directories
# This goes through backup_directory and finds any directories
# older than one week (up to one year) and removes them.
def rotate():
    for i in range(7, 365):
        remove = today - timedelta(i)
        directory = "%s/%s" % (backup_directory, remove)
        if debug: print directory
        if os.path.exists(directory):
            cmd = "rm -rf %s" % directory
            subprocess.call(cmd, shell=True)
    return;


# The main program
def main():
    make_connection()
    for container in containers:
        if debug: print "Backing up: %s" % container
        create_directory(container)
        get_container(container)
#    rotate()


if __name__ == '__main__':
    main()
