#!/usr/bin/python
# Copyright (c) 2006 Red Hat, Inc. All rights reserved. This copyrighted material 
# is made available to anyone wishing to use, modify, copy, or 
# redistribute it subject to the terms and conditions of the GNU General 
# Public License v.2.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Author: Bill Peck
#

import sys, getopt
import xmlrpclib
import string
import os
import commands
import pprint
import math

sys.path.append('.')
sys.path.append("/usr/lib/anaconda")
import smolt
import anaconda_log
import partedUtils

USAGE_TEXT = """
Usage:  push-inventory.py -h <HOSTNAME>
"""

def push_inventory(hostname, inventory):
   session = xmlrpclib.Server(lab_server, allow_none=True)
   try:
      resp = session.legacypush(hostname, inventory)
      if(resp != 0) :
         raise NameError, "ERROR: Pushing Inventory for host %s." % hostname
   except:
      raise

def read_inventory():
    # get the data from SMOLT but modify it for how RHTS expects to see it
    # Eventually we'll switch over to SMOLT properly.
    data = {}
    data['MODULE'] = []
    data['CPUFLAGS'] = []
    data['PCIID'] = []
    data['USBID'] = []
    data['HVM'] = False
    data['DISK'] = []
    data['DISKSPACE'] = 0
    data['NR_DISKS'] = 0

    cpu_info = smolt.read_cpuinfo()
    memory   = smolt.read_memory()
    profile  = smolt.Hardware()

    data['ARCH'] = cpu_info['platform']
    data['CPUSPEED'] = cpu_info['speed']
    try:
        data['CPUFAMILY'] = cpu_info['model_number']
    except:
        data['CPUFAMILY'] = cpu_info['model_rev']
    data['CPUVENDOR'] = cpu_info['type']
    data['CPUMODEL'] = cpu_info['model']
    data['CPUMODELNUMBER'] = cpu_info['model_ver']
    data['PROCESSORS'] = cpu_info['count']
    data['VENDOR'] = "%s" % profile.host.systemVendor
    data['MODEL'] = "%s" % profile.host.systemModel
    data['FORMFACTOR'] = "%s" % profile.host.formfactor

    # Round memory up to the next base 2
    n=0
    memory = int(memory['ram'])
    while memory > ( 2 << n):
        n=n+1
    data['MEMORY'] = 2 << n

    for cpuflag in cpu_info['other'].split(" "):
        data['CPUFLAGS'].append(cpuflag)

    for VendorID, DeviceID, SubsysVendorID, SubsysDeviceID, Bus, Driver, Type, Description in profile.deviceIter():
       if VendorID and DeviceID:
           if Bus == "pci":
               data['PCIID'].append("%04x:%04x" % ( VendorID, DeviceID))
           if Bus == "usb":
               data['USBID'].append("%04x:%04x" % ( VendorID, DeviceID))

    modules =  commands.getstatusoutput('/sbin/lsmod')[1].split('\n')[1:]
    for module in modules:
        data['MODULE'].append(module.split()[0])

    # checking for whether or not the machine is hvm-enabled.
    caps = ""
    if os.path.exists("/sys/hypervisor/properties/capabilities"):
        caps = open("/sys/hypervisor/properties/capabilities").read()
        if caps.find("hvm") != -1:
           data['HVM'] = True

    # calculating available diskspace 
    diskset = partedUtils.DiskSet()
    diskset.openDevices()
    for diskname in diskset.disks.keys():
        disksize = int(math.ceil(partedUtils.getDeviceSizeMB(diskset.disks[diskname].dev)))
        data['DISK'].append("%d " % (disksize))
        data['DISKSPACE'] += disksize
        data['NR_DISKS'] += 1


    return data

def usage():
    print USAGE_TEXT
    sys.exit(-1)

def main():
    global lab_server, hostname

    lab_server = None
    server = None
    user = None
    password = None
    hostname = None
    debug = 0

    if ('PASSWORD' in os.environ.keys()):
        password = os.environ['PASSWORD']
    if ('USER' in os.environ.keys()):
        user = os.environ['USER']
    if ('LAB_SERVER' in os.environ.keys()):
        server = os.environ['LAB_SERVER']
    if ('HOSTNAME' in os.environ.keys()):
        hostname = os.environ['HOSTNAME']

    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, 'dh:S:u:p:', ['server=','user=','password='])
    except:
        usage()
    for opt, val in opts:
        if opt in ('-d', '--debug'):
            debug = 1
        if opt in ('-h', '--hostname'):
            hostname = val
        if opt in ('-S', '--server'):
            server = val
        if opt in ('-u', '--user'):
            user = val
        if opt in ('-p', '--password'):
            password = val

    if not hostname:
        print "You must sepcify a hostname with the -h switch"
        sys.exit(1)

    if not server:
        print "You must sepcify a lab_server with the -S switch"
        sys.exit(1)

    if not user:
        print "You must sepcify a user with the -u switch"
        sys.exit(1)

    if not password:
        print "You must sepcify a password with the -p switch"
        sys.exit(1)

    lab_server = "https://%s:%s@%s/RPC2" % (user,password,server)
    inventory = read_inventory()
    if debug:
        print inventory
    else:
        push_inventory(hostname, inventory)


if __name__ == '__main__':
    main()
    sys.exit(0)
