#! /usr/bin/env python
# SHARK agent 
#
# daemon on target machine, after requestede, execute cmds to
# collect perf data and write to datafile, sending files back 
# to server
#
import socket
import time
import os

# cmd strings needed to execute on client machines
#
cmdstrings = "sar -n DEV 1 10 > /tmp/sarnDEV-", \
			 "iostat 1 10 > /tmp/iostat-",	\
			 "sar -B 1 10 > /tmp/sarB-",	\
			 "sar -P ALL 1 10 > /tmp/sarPALL-",	\
			 "vmstat 1 10 > /tmp/vmstat-"

# listen socket to accept cmd connection where get passwd 
# and requestid.  if connection accepted, end blocking
#
listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_sock.bind(('',7778))
listen_sock.listen(25)
cmd_sock,caddr = listen_sock.accept()

# handshake to verify passwd
# cmd socket to get cmd string
#
while True:
	cmdstr = cmd_sock.recv(12)
	if cmdstr[0:6] == 'qwe123':
		break

print cmdstr

idstring = cmdstr[cmdstr.find("+")+1:]

cmd_sock.close()


# listen socket 2 to accept data connection
#
listen_sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_sock2.bind(('',7777))
listen_sock2.listen(25)
data_sock,daddr = listen_sock2.accept()

# execute cmds 
#
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

	# send magic and filename
	#
	sended = data_sock.send("SHARK"+file_name)
	if sended != (len(file_name) + 5):
		print "send file name failed"
		exit()
	time.sleep(2)
	
	# loops to send file data
	#
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
