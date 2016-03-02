#!/usr/bin/python -tt
# vim: set ts=4 sw=4 tw=79 et :

# dns_update.py
#
# This program manages updating files for BIND based on updates from the
# vnr-configs repo.
#
# Workflow approach:
#  - pull git repo
#  - backup files
#  - update/remove files
#  - run named checkconfig
#  - restart named
#  - do nslookup tests
#  - if failed, replace with backup
#
# Created by George Hicks II


from datetime import date, timedelta
import os
import socket
import subprocess


# Global Variables
debug = False
git_dir = '/root/vnr-configs'
backup_directory = '/root/named'
etc_dir = "%s/etc" % backup_directory
var_dir = "%s/var/named" % backup_directory
repo_url = 'https://github.com/hicksg/vnr-configs.git'


# Backup important BIND files
def bind_backup():
    global etc_dir, var_dir
    if (create_dir(etc_dir) and 
        sync_dir("/etc/named*", "%s/" % etc_dir) and
        create_dir(var_dir) and
        sync_dir("/var/named/master", "%s/" % var_dir)):
        return True;
    print "(bind_backup)\tFAILED to backup existing configuration"
    return False;


# Replace existing configuration with repo
# The direction is either from the git repo (repo)
# or the backup (backup).
def bind_replace(direction):
    global debug, git_dir, etc_dir, var_dir
    if direction == "repo":
        if (sync_dir("%s/dns01/etc/named*" % git_dir, "/etc/") and
            fix_selinux("/etc/named*") and
            fix_owner("/etc/named*", "root:named") and
            sync_dir("%s/dns01/var/named/master" % git_dir, "/var/named/") and
            fix_selinux("/var/named/master") and
            fix_owner("/var/named/master", "root:named")):
            return True;
        print "(bind_replace)\tFAILED to sync repo to live"
        return False;
    elif direction == "backup":
        if (sync_dir("%s/named*" % etc_dir, "/etc/") and
            fix_selinux("/etc/named*") and
            fix_owner("/etc/named*", "root:named") and
            sync_dir("%s/master" % var_dir, "/var/named/") and
            fix_selinux("/var/named/master") and
            fix_owner("/var/named/master", "root:named")):
            return True;
        print "(bind_replace)\tFAILED to restore backup to live"
        return False;
    else:
        print "(bind_replace)\t%s is an invalid direction" % direction
        return False;
    return True;


# Restart BIND service
def bind_restart():
    cmd = "service named restart"
    return run_cmd("bind_restart", cmd);



# Do a series of lookups to test the BIND service
def bind_test():
    local_ip = get_local_ip()
    sites = ['www.phenona.com',
             'www.stackato.com',
             'www.stackato.io',
             'www.usepaas.com',
             'ports.stacka.to']
    for site in sites:
        cmd = "/usr/bin/nslookup %s %s" % (site, local_ip)
        retcode = run_cmd("bind_test", cmd)
        if not retcode:
           break 
    return retcode;


# Check the configuration
def checkconfig():
    cmd = "service named checkconfig"
    return run_cmd("checkconfig", cmd);


# Create a set of directories
def create_dir(directory):
    global debug
    if not os.path.exists(directory):
        if debug: print "(create_dir)\tCreating %s" % directory
        try:
            os.makedirs(directory)
        except:
            print "(create_dir)\tFAILED create %s" % directory
            return False;
    return True;


# Print a failure message and quit
def fail(message):
    raise SystemExit(message)
    return;


# Fallback to the backup configuration
def fallback():
    if (bind_replace("backup") and
        checkconfig() and
        bind_restart() and
        bind_test()):
        return;
    fail("(main)\t\tFAILED TO RESTORE BACKUP, FIX NAMED!!!!")


# Fix the selinux settings for files/directories
def fix_selinux(directory):
    cmd = "/sbin/restorecon -r %s" % directory
    return run_cmd("fix_selinux", cmd);


# Fix the ownership of files/directories
def fix_owner(directory, owner):
    global debug
    cmd = "/bin/chown -R %s %s" % (owner, directory)
    return run_cmd("fix_owner", cmd);


# Find out the IP of this machine for testing
def get_local_ip():
    return socket.gethostbyname(socket.getfqdn());


# Pull the git repo
def git_pull():
    global git_dir, repo_url
    if not os.path.exists(git_dir):
        cmd = "cd /root && /usr/bin/git clone %s" % repo_url
        return run_cmd("git_pull", cmd);
    else:
        cmd = "cd %s && /usr/bin/git pull" % git_dir
        return run_cmd("git_pull", cmd);
    return True;


# Run a given command
def run_cmd(caller, cmd):
    if debug: print "(%s)\tExecuting -> %s" % (caller, cmd)
    retcode = subprocess.call(cmd, shell=True)
    if retcode > 0:
        print "(%s)\tFAILED %s" % (caller, cmd)
        return False;
    return True;


# Sync directories.
def sync_dir(source, target):
    cmd = "/usr/bin/rsync -aq --delete %s %s" % (source, target)
    return run_cmd("sync_dir", cmd);


# The main program
def main():
    if not git_pull():
        fail("(main)\t\tFAILED TO GET THE REPOSITORY....QUITTING")
    if not bind_backup():
        fail("(main)\t\tFAILED TO BACKUP ORIGINALS....QUITTING")
    if not bind_replace("repo"):
        print "(main)\t\tFAILED TO UPDATE, FALLING BACK"
        fallback()
    if not checkconfig():
        print "(main)\t\tFAILED CHECK, FALLING BACK"
        fallback()
    if not bind_restart():
        print "(main)\t\tFAILED RESTART, FALLING BACK"
        fallback()
    if not bind_test():
        print "(main)\t\tFAILED TESTING, FALLING BACK"
        fallback()
    return;


if __name__ == '__main__':
    main()

