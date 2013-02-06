#! /usr/bin/env python
import socket
import time
import os

cmdstrings = "sar -n DEV 1 10 > /tmp/sarnDEV-", \
			 "iostat 1 10 > /tmp/iostat-",	\
			 "sar -B 1 10 > /tmp/sarB-",	\
			 "sar -P ALL 1 10 > /tmp/sarPALL-",	\
			 "vmstat 1 10 > /tmp/vmstat-"

cmdsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cmdsock.bind(('',7778))
cmdsock.listen(5)
cs,caddr = cmdsock.accept()
while True:
	cmdstr = cs.recv(12)
	if cmdstr[0:6] == 'qwe123':
		break
	time.sleep(2)

print cmdstr

idstring = cmdstr[cmdstr.find("+")+1:]

cs.close()

sersock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sersock.bind(('',7777))
sersock.listen(5)
ds,daddr = sersock.accept()

for cs in cmdstrings:
	ns = cs + idstring
	print ns
	ret = os.system(ns)
	ret = 0
	if ret != 0:
		print ns+"  error"
		exit()
	
	fs = ns[ns.find("/tmp"):]
	print fs
	fn = open('/tmp/sar')
	while True:
		data = fn.read(1024)
		if not data:
			break
		while len(data) > 0:
			sended = ds.send(data)
			data = data[sended:]
	
	time.sleep(2)
	ds.send('EOF')
	fn.close()
	
ds.close()
