#!/usr/local/bin/python2.7 -tt
# vim: set ts=4 sw=4 tw=79 et :

# container_download.py
#
# Originally conceived as a program for downloading
# object containers from Openstack, it currently
# manages downloading bucket objects from S3 (AWS).
#
# The approach for managing backups is as follows:
# - find the latest backup directory for the container
# - create a backup directory for today
# - get the contents of the container, for each file:
#   - check if the file exists locally
#     - if it does not, download it
#     - if it does, compare checksums
#       - if they differ, download it
#       - if not, hard link it
# rotate the downloads
#
# Created by George Hicks II


from datetime import date, timedelta
import binascii
import boto3
import botocore
import hashlib
import os
import subprocess


# Global Variables
debug = False
backup_directory = '/data/containers'
containers = ['patches.stackato.com', 'downloads.stackato.com']
today = date.today()
latest = ''
client = ''


# Check local file
# This checks if the local copy of the file exists.
def check_local(filename):
    global debug, backup_directory, latest
    if debug: print "Checking locality %s/%s/%s" % (backup_directory,
                                                    latest, filename)
    result = False
    if ((latest != '') and (os.path.isfile("%s/%s/%s" % (backup_directory,
                                                         latest, filename)))):
        result = True
    return result;


# Create directory
# This creates the full directory structure for:
#    backup_directory/today's date/supplied subdirectories
# This can be leveraged to create a full path for container
# objects.
def create_directory(subdirectory):
    global debug, backup_directory, today
    if debug: print "Creating directory: %s/%s/%s" % (backup_directory,
                                                      today.isoformat(),
                                                      subdirectory)
    directory = "%s/%s/%s" % (backup_directory, today.isoformat(), subdirectory)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return;


# Create subdirectories
# This leverages the create_directory function to create subdirectories
# as needed.
def create_subdirectories(object_name, container):
    subdirs = object_name.split('/')
    if len(subdirs) > 1:
        create_directory("%s/%s" % (container, '/'.join(subdirs[:-1])))
    return;


# Find the latest backup
# This finds the diretory of the most recent backup that is not today.
def find_latest():
    global debug, backup_directory, latest, today
    lyear = 0
    lmonth = 0
    lday = 0
    tyear, tmonth, tday = today.isoformat().split('-')
    if debug: print "Looking for latest..."
    for directory in os.listdir(backup_directory):
        if debug: print "  -> %s" % directory
        try:
            year, month, day = directory.split('-')
        except:
            continue
        try:
            int(year)
            int(month)
            int(day)
        except:
            continue
        if (int(year) == int(tyear) and
            int(month) == int(tmonth) and
            int(day) == int(tday)):
            continue
        if int(year) > int(lyear):
            lyear = year
            lmonth = month
            lday = day
        elif int(year) == int(lyear):
            if int(month) > int(lmonth):
                lmonth = month
                lday = day
            elif int(month) == int(lmonth):
                if int(day) > int(lday):
                    lday = day
    if lyear == 0 or lmonth == 0 or lday == 0:
        latest = ''
        if debug: print "No valid latest backup"
    else:
        latest = "%s-%s-%s" % (lyear, lmonth, lday)
        if debug: print "Found %s" % latest
    return;


# Get the container contents
# This downloads the contents of the specified container into
# <backup_directory>/<today>/<container>
def get_container(container):
    global debug, client
    if debug: print "get_container: %s" % container
    try:
        bucket = client.list_objects(Bucket=container)
    except botocore.exceptions.ClientError, e:
        print e
        print "%s bucket does not exist!" % (container)
        return;
    for key in bucket['Contents']:
        if key['Key'][-1] == '/':
            # This weeds out any objects that are directories not files.
            continue
        if check_local("%s/%s" % (container, key['Key'])):
            if debug: print "%s exists locally, checking..." % key['Key']
            s3sum = s3_md5sum(key['Key'], container)
            if '-' in s3sum:
                localsum = local_s3sum(key['Key'], container)
            else:
                localsum = local_md5sum(key['Key'], container)
            if s3sum == localsum:
                link_local(key['Key'], container)
            else:
                get_s3_object(key['Key'], container)
        else:
            if debug: print "Downloading %s" % key['Key']
            get_s3_object(key['Key'], container)
    return;


# Get a file from an S3 bucket
# Download a file from an S3 bucket and create directories
# to contain it as needed.
def get_s3_object(object_name, container):
    global debug, backup_directory, client, today
    directory = "%s/%s/%s" % (backup_directory, today.isoformat(), container)
    create_subdirectories(object_name, container)
    file_location = "%s/%s" % (directory, object_name)
    if debug: print file_location
    client.download_file(container, object_name, file_location)
    return;


# Link local file
# This will hard link a previous backup file to today's location.
def link_local(object_name, container):
    global debug, backup_directory, today, latest
    src = "%s/%s/%s/%s" % (backup_directory, latest, container, object_name)
    dest = "%s/%s/%s/%s" % (backup_directory, today.isoformat(), container,
                            object_name)
    if debug: print "Linking %s to %s" % (src, dest)
    create_subdirectories(object_name, container)
    cmd = "ln %s %s" % (src, dest)
    subprocess.call(cmd, shell=True)
    return;


# Local md5sum
# Calculate and return the checksum of a local file.
def local_md5sum(object_name, container):
    global debug, backup_directory, latest
    blocksize=65536
    hasher = hashlib.md5()
    filehandle = open("%s/%s/%s/%s" % (backup_directory, latest, container,
                                        object_name), 'rb')
    for block in iter(lambda: filehandle.read(blocksize), ""):
        hasher.update(block)
    filehandle.close()
    if debug: print "Local md5sum: %s" % hasher.hexdigest()
    return hasher.hexdigest();


# S3 md5sum of local file
# This will calculate the S3 checksum of a local file.
# Useful in cases where S3 has not done a standard md5sum.
def local_s3sum(object_name, container):
    global debug, backup_directory, latest
    blocksize = 15728640 # this assumes 15MB upload blocks
    block_count = 0
    md5string = ""
    filehandle = open("%s/%s/%s/%s" % (backup_directory, latest, container,
                                        object_name), 'rb')
    for block in iter(lambda: filehandle.read(blocksize), ""):
        hasher = hashlib.md5()
        hasher.update(block)
        md5string = md5string + binascii.unhexlify(hasher.hexdigest())
        block_count += 1
    filehandle.close()
    hasher = hashlib.md5()
    hasher.update(md5string)
    s3sum = hasher.hexdigest() + "-" + str(block_count)
    if debug: print "Local s3sum: %s" % s3sum
    return s3sum;


# Make a connection to AWS.
def make_connection():
    global client
    client = boto3.client('s3')
    return;


# Rotate directories
# This goes through backup_directory and finds any directories
# older than one week (up to one year) and removes them.
def rotate():
    global debug, backup_directory, today
    for i in range(7, 365):
        remove = today - timedelta(i)
        directory = "%s/%s" % (backup_directory, remove)
        if debug: print directory
        if os.path.exists(directory):
            cmd = "rm -rf %s" % directory
            subprocess.call(cmd, shell=True)
    return;


# S3 md5sum
# Calculate and return the checksum of an S3 object
def s3_md5sum(object_name, container):
    global debug, client
    try:
        md5sum = client.head_object(Bucket=container,
                                    Key=object_name)['ETag'][1:-1]
    except botocore.exceptions.ClientError:
        md5sum = ''
    if debug: print "S3 md5sum: %s" % md5sum
    return md5sum;


# The main program
def main():
    global debug
    find_latest()
    make_connection()
    for container in containers:
        if debug: print "Backing up: %s" % container
        create_directory(container)
        get_container(container)
    rotate()


if __name__ == '__main__':
    main()



