#! /usr/bin/env python
import socket
import time
import os

cmdstrings = "sar -n DEV 1 10 > /tmp/sarnDEV-", \
			 "iostat 1 10 > /tmp/iostat-",	\
			 "sar -B 1 10 > /tmp/sarB-",	\
			 "sar -P ALL 1 10 > /tmp/sarPALL-",	\
			 "vmstat 1 10 > /tmp/vmstat-"

listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_sock.bind(('',7778))
listen_sock.listen(5)
cmd_sock,caddr = listen_sock.accept()
while True:
	cmdstr = cmd_sock.recv(12)
	if cmdstr[0:6] == 'qwe123':
		break

print cmdstr

idstring = cmdstr[cmdstr.find("+")+1:]

cmd_sock.close()

listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_sock.bind(('',7777))
listen_sock.listen(5)
data_sock,daddr = listen_sock.accept()

for cmdstring in cmdstrings:
	cmds = cmdstring + idstring
	print cmds
	ret = os.system(cmds)
	if ret != 0:
		print cmds+"  error"
		data_sock.close()
		exit()
	
	file_name = cmds[cmds.find("/tmp"):]
	print file_name

	sended = data_sock.send("SHARK"+file_name)
	if sended != (len(file_name) + 5):
		print "send file name failed"
		exit()
	time.sleep(2)
	
	open_file = open(file_name)
	while True:
		data = open_file.read(1024)
		if not data:
			break
		while len(data) > 0:
			sended = data_sock.send(data)
			data = data[sended:]
	
	time.sleep(2)
	data_sock.send('EOF')
	open_file.close()
	
data_sock.close()
