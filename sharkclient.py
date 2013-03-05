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
import syslog

# cmd strings needed to execute on client machines
#
cmdstrings = "sar -n DEV 1 10 > /tmp/sarnDEV-", \
			 "iostat 1 10 > /tmp/iostat-",	\
			 "sar -B 1 10 > /tmp/sarB-",	\
			 "sar -P ALL 1 10 > /tmp/sarPALL-",	\
			 "vmstat 1 10 > /tmp/vmstat-"

# shark server addr, get from listen
#
# server_addr = tuple()

# multithreads to run cmds, like sar -P ALL ..
# this is the class to implmt multirhread
#
class shark_client_thread(threading.Thread):
	cmdstring = ""
	
	def __init__(self, cs):
		threading.Thread.__init__(self)
		self.cmdstring = cs
	
	def run(self):
		if self.cmdstring == "":
			print 'cmdstring null exit'
			syslog.syslog(syslog.LOG_DEBUG, 'cmdstring null exit')
			exit()

		ret = os.system(self.cmdstring)
		if ret != 0:
			syslog.syslog(syslog.LOG_DEBUG, 'system exe error')
			print 'system exe error'
			exit()


# execute cmds on client machine multithread way
#
def execute_perf_cmds(idstr):
	sthreads = {}
	for cs in cmdstrings:
		cmdstring = cs + idstr
		print 'executing ' + cmdstring
		syslog.syslog(syslog.LOG_DEBUG, 'executing ' + cmdstring)

		sthreads[cs] = shark_client_thread(cmdstring)
		sthreads[cs].start()

	for cs in cmdstrings:
		sthreads[cs].join()
	print 'end exec cmds'
	syslog.syslog(syslog.LOG_DEBUG, 'exec cmds end')

# listen socket to accept cmd connection where get passwd 
# and requestid.  if connection accepted, end blocking
#
def get_idstr():
	os.system('hostname > /tmp/hn')
	hnfile = open('/tmp/hn')
	host_name = string.rstrip(hnfile.readline(), '\n')
	hnfile.close()

	dtstr = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')

	listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listen_sock.bind(('',7778))
	listen_sock.listen(5)
	cmd_sock,cmd_addr = listen_sock.accept()
	#print 'cmdaddr',
	#print cmd_addr
	server_addr = cmd_addr[0]
	
	# handshake to verify passwd 
	# cmd socket to get cmd string
	#
	while True:
		cmdstr = cmd_sock.recv(12)
		if cmdstr[0:6] == 'qwe123':
			break
	
	cmd_sock.close()
	listen_sock.close()

	idstr = cmdstr[cmdstr.find("+")+1:] + '-' + host_name + '-' + dtstr 
	rt_t = (idstr, server_addr)
	syslog.syslog(syslog.LOG_DEBUG, 'get_idstr returned: ' + rt_t[0] \
		+ rt_t[1])
	return rt_t


# handle send_files error
#
def sf_error(errstr, data_sock):
	print errstr
	syslog.syslog(syslog.LOG_DEBUG, errstr)
	data_sock.close()
	exit()

# connect to server to send files
#
def send_files(idstr_sd_t):
	#
	# use magic coming addr
	#
	data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print 'send_files beagin idstr: ' + idstr_sd_t[0] + 'server ip: ' + \
	idstr_sd_t[1]
	syslog.syslog(syslog.LOG_DEBUG, 'send_files beagin idstr: ' + \
	idstr_sd_t[0] + 'server ip: ' + idstr_sd_t[1])
	data_sock.connect((idstr_sd_t[1], 7777)) 
	
	# five files to transfer
	#
	for cs in cmdstrings:
		cmds = cs + idstr_sd_t[0]
		
		# get file name and size, check
		#
		file_name = cmds[cmds.find("/tmp")+5:]

		file_size = 0
		stat_rt = os.stat(cmds[cmds.find("/tmp"):])
		if stat_rt != None and stat_rt.st_size !=0:
			file_size = stat_rt.st_size
		else:
			sf_error('stat error', data_sock)

		print 'file name: '+file_name
		print 'file size ' + repr(file_size)
		syslog.syslog(syslog.LOG_DEBUG, 'file name: '+file_name)
		syslog.syslog(syslog.LOG_DEBUG, 'file size ' + repr(file_size))
	
		if len(file_name) > 200:
			print 'file name too long: ' + file_name
			syslog.syslog(syslog.LOG_DEBUG, 'file name too long: ' + \
			file_name)
			continue

		if file_size > 9000000:
			syslog.syslog(syslog.LOG_DEBUG, 'file size too big: ' + \
			repr(file_size))
			print 'file size too big: ' + repr(file_size)
			continue

		# send magic and filename length 
		#
		sended = 0
		magic_str = "SHARK" + repr(len(file_name) + 100)
		syslog.syslog(syslog.LOG_DEBUG, magic_str + " magic str sending")
		sended = data_sock.send(magic_str)
		if sended != 8:
			sf_error('send magic failed', data_sock)

		time.sleep(2)
		
		# send filenme
		#
		sended = 0
		sended = data_sock.send(file_name)
		syslog.syslog(syslog.LOG_DEBUG, file_name + " str sended")
		if sended != (len(file_name)):
			sf_error('send file name failed', data_sock)

		time.sleep(2)
		
		# send magic and file size
		#
		sended = 0
		magic_str2 = "SHARK2" + repr(file_size + 1000000)
		print 'magic2 ' + string.rstrip(magic_str2, 'L')
		syslog.syslog(syslog.LOG_DEBUG, 'magic2 ' + string.rstrip(magic_str2, 'L'))
		sended = data_sock.send(string.rstrip(magic_str2, 'L'))
		if sended != 13:
			sf_error('send magic2 failed', data_sock)

		time.sleep(2)
		
		# loops to send file data
		#
		open_file = open('/tmp/' + file_name)
		total_sended = 0
		while True:
			data = open_file.read(128)
			if not data:
				break
			while len(data) > 0 and total_sended < file_size:
				sended = data_sock.send(data)
				data = data[sended:]
				total_sended += sended
		
		#time.sleep(2)
		#data_sock.send('EOF')
		open_file.close()
		time.sleep(5)
	
	data_sock.close()


def main():
	while True:
		get_t = []
		get_t = get_idstr();
		if len(get_t[0]) <= 0:
			syslog.syslog(syslog.LOG_DEBUG, "get idstr failed")
			print 'get idstr failed'
			exit()
		#print 'idstr '+get_t[0]
		#print 'sv ip '+get_t[1]

		# execute cmds and send files
		execute_perf_cmds(get_t[0])
		#print 'aft exe sd',
		#print 'idstr '+get_t[0]
		#print 'sv ip '+get_t[1]
		time.sleep(2)
	
		# send cmd-result files to server
		send_files(get_t)

if __name__ == '__main__':
	syslog.openlog("SHARK", facility=syslog.LOG_USER)
	main()
	syslog.closelog()
