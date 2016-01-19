#!/usr/bin/python -tt
# vim: set ts=4 sw=4 tw=79 et :

from datetime import date, timedelta
import os
import subprocess


# Global Variables
debug = False
backup_directory = '/data/containers'
containers = ['kato-patch-blob', 'kato-patch-blob-dev']
today = date.today()


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
    os.chdir(directory)
    cmd = ('/usr/local/bin/swift'
           ' --os-auth-url https://region-a.geo-1.identity.hpcloudsvc.com:35357/v2.0/'
           ' --os-password brBt13xpqs22'
           ' --os-region-name region-b.geo-1'
           ' --os-tenant-id 55587226903523'
           ' --os-tenant-name hpcs@activestate.com-tenant1'
           ' --os-username build-services'
           ' -V 2.0 download')
    cmd = "%s %s" % (cmd, container)
    if debug: print "get_container: %s" % cmd
    subprocess.call(cmd, shell=True)
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
    for container in containers:
        if debug: print "Backing up: %s" % container
        create_directory(container)
        get_container(container)
    rotate()


if __name__ == '__main__':
    main()

