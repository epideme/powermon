#!/usr/bin/python
import time
import getpass
import sys
#import telnetlib
#import MySQLdb
import os
import subprocess
from PyNUT import PyNUTClient
client = PyNUTClient()
keeptrack=dict()

esxserver = "esxservername"
lastshutdown = "name_of_VSA"
noshutdown = "name_of_nutserver"
upsname = "name_of_UPS_in_nut"

offlinecount=0
onlinecount=0
togo=0
alldown=0
minruntime=600

upsvars = client.GetUPSVars(upsname)
runtime = upsvars['battery.runtime']

while int(runtime) > int(minruntime):
  #print upsvars['ups.status']
  if upsvars['ups.status'] != "OL":
    print "Offline. Runtime:", runtime
  else:
    print "Online. Runtime:", runtime
    sys.exit()
  time.sleep(10)
  upsvars = client.GetUPSVars(upsname)
  runtime = upsvars['battery.runtime']

while alldown == 0:
  cmd = "esxcli vm process list | grep Display | awk '{print $3, $4}'"
  #getrunning = os.system(cmd)
  getrunning = subprocess.Popen(["ssh" , "%s" % esxserver, cmd], shell=False, stdout=subprocess.PIPE)
  running = getrunning.stdout.readlines()
  running = map(lambda s: s.strip(), running)
  for vm in running:
    if vm == lastshutdown:
      print "Not yet shutting down:", vm
    elif vm == noshutdown:
      print "Not shutting down:", vm
    else:
      togo += 1
      if vm in keeptrack:
        keeptrack[vm] +=1
	if keeptrack[vm] > 30:
          print "Kill VM:", vm
          cmd = "vim-cmd vmsvc/getallvms | grep '" + vm + "' | cut -d ' ' -f 1 | xargs vim-cmd vmsvc/power.off"
          subprocess.Popen(["ssh" , "%s" % esxserver, cmd], shell=False, stdout=subprocess.PIPE)
          #print cmd
      else:
        print "Shutting down:", vm
        cmd = "vim-cmd vmsvc/getallvms | grep '" + vm + "' | cut -d ' ' -f 1 | xargs vim-cmd vmsvc/power.shutdown"
        subprocess.Popen(["ssh" , "%s" % esxserver, cmd], shell=False)
        #print cmd
        keeptrack[vm] = 1

  print "To go:",togo
  if togo == 0:
    alldown = 1
    print "Shutting down:", lastshutdown
    cmd = "vim-cmd vmsvc/getallvms | grep '" + lastshutdown + "' | cut -d ' ' -f 1 | xargs vim-cmd vmsvc/power.shutdown"
    subprocess.Popen(["ssh" , "%s" % esxserver, cmd], shell=False, stdout=subprocess.PIPE)
    #print cmd
  else:
    togo = 0
  # print keeptrack
  time.sleep(10);

while onlinecount<3:
  upsvars = client.GetUPSVars(upsname)
  print upsvars['ups.status']
  if upsvars['ups.status'] == "OL":
    onlinecount += 1
    print "Power restored, waiting 30s"
  else:
    onlinecount = 0
    print "No Power, waiting..."
  time.sleep(10)

print "Rebooting:", esxserver
cmd = "reboot"
subprocess.Popen(["ssh" , "%s" % esxserver, cmd], shell=False, stdout=subprocess.PIPE)

print "Done"
