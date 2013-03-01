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
import string
from datetime import datetime
import threading

# cmd strings needed to execute on client machines
#
cmdstrings = "sar -n DEV 1 10 > /tmp/sarnDEV-", \
			 "iostat 1 10 > /tmp/iostat-",	\
			 "sar -B 1 10 > /tmp/sarB-",	\
			 "sar -P ALL 1 10 > /tmp/sarPALL-",	\
			 "vmstat 1 10 > /tmp/vmstat-"

# multithreads to run cmds, like sar -P ALL ..
# this is the class to implmt multirhread
#
class shark_thread(threading.Thread):
	cmdstring = ""
	
	def __init__(self, cs):
		threading.Thread.__init__(self)
		self.cmdstring = cs
	
	def run(self):
		if self.cmdstring == "":
			print 'cmdstring null exit'
			exit()

		ret = os.system(self.cmdstring)
		if ret != 0:
			print 'system exe error'
			exit()


# execute cmds on client machine multithread way
#
def execute_perf_cmds(idstr):
	sthreads = {}
	for cs in cmdstrings:
		cmdstring = cs + idstr
		print 'executing ' + cmdstring

		sthreads[cs] = shark_thread(cmdstring)
		sthreads[cs].start()

	for cs in cmdstrings:
		sthreads[cs].join

# listen socket to accept cmd connection where get passwd 
# and requestid.  if connection accepted, end blocking
#
def get_idstr():
	os.system('hostname > /tmp/hn')
	hnfile = open('/tmp/hn')
	host_name = string.rstrip(hnfile.readline(), '\n')
	hnfile.close()

	dtstr = datetime.strftime(datetime.now(), '-%y%m%d_%H%M%S-')

	listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listen_sock.bind(('',7778))
	listen_sock.listen(5)
	cmd_sock,caddr = listen_sock.accept()
	
	# handshake to verify passwd # cmd socket to get cmd string
	#
	while True:
		cmdstr = cmd_sock.recv(12)
		if cmdstr[0:6] == 'qwe123':
			break
	
	cmd_sock.close()
	listen_sock.close()

	idstr = cmdstr[cmdstr.find("+")+1:] + dtstr + host_name 
	return idstr


# listen socket 2 to accept data connection
#
def send_files(idstr):
	listen_sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listen_sock2.bind(('',7777))
	listen_sock2.listen(5)
	data_sock,daddr = listen_sock2.accept()
	
	for cs in cmdstrings:
		cmds = cs + idstr
		file_name = cmds[cmds.find("/tmp")+5:]
		print 'fn: '+file_name
	
		# send magic and filename
		#
		sended = data_sock.send("SHARK"+file_name)
		if sended != (len(file_name) + 5):
			print "send file name failed"
			data_sock.close()
			listen_sock2.close()
			exit()
		time.sleep(2)
		
		# loops to send file data
		#
		open_file = open('/tmp/' + file_name)
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
	listen_sock2.close()


def main():
	while True:
		idstr = get_idstr();
		if len(idstr) <= 0:
			print 'get idstr failed'
			exit()
		print 'idstr '+idstr

		# execute cmds and send files
		execute_perf_cmds(idstr)
	
		# send cmd-result files to server
		send_files(idstr)

if __name__ == '__main__':
	main()
