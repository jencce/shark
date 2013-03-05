#! /usr/bin/env python
# SHARK server 
# 
# execute on any machine, request to SHARK agents to get 
# performance data files 
#
import socket
import time
import os
import re
import string import threading

# get requestid string from user to uniq this request
# for result file storage
# interactive or read config file
#
def get_idstr():
	id_string = raw_input("input 4 chars request idstring:")
	while len(id_string) != 4:
		id_string = raw_input("input 4 chars request idstring:")
	return id_string

# read conf to get clientip list
#
def read_conf():
	config_file = open("shark.conf")
	for conf_item in config_file:
		print conf_item,
		find_clientip = conf_item.find("clientip")
		find_comment = conf_item.find("#")
		if find_comment == 0:
			continue
		if find_clientip == 0:
			client_ip_list = conf_item.split()
			return client_ip_list


# cmdsocket to shake hands with clients
# predef string as passwd
# passwd and requestid string as magic words
#
def send_magic(clientip, idstr):
	try:
		cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		cmd_sock.connect((clientip,7778)) 
		cmd_sock.send("qwe123+"+idstr)
		cmd_sock.close()
	except socket.error as err:
		print err
		return -1


# use data socket to recv result files
#
def old_recv_files(file_cnt):
	listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listen_sock.bind(('',7777))
	listen_sock.listen(5)
	data_sock,daddr = listen_sock.accept()
	
	# if connected, file files to be recved each connection
	#
	file_counter = 5
	while file_counter > 0:
		file_counter = file_counter - 1
		raw_file_name = ""
	
		# recv file name with magic "SHARK"
		#
		raw_file_name = data_sock.recv(100)
		if raw_file_name.find("SHARK") != -1:
			file_name = raw_file_name[raw_file_name.find("SHARK")+5:]
			print "newfs " + file_name
		else:
			print "recv filename failed"
			data_sock.close()
			exit()
		
		# create new file ,recv data with results
		# write file
		#
		os.system('mkdir -p /tmp/SHARK/')
		openfile = open('/tmp/SHARK/'+file_name, 'w')
		while True:
			data = data_sock.recv(1024)
		#	print 'data: {}, lenth {}'.format(data[0:2], len(data))
			if data == 'EOF':
				break
			openfile.write(data)
		
		openfile.close()
	
	data_sock.close()
	print ' done'

# multithread recving files
#
class shark_server_thread(threading.Thread):
	#
	# socket to recv data as params
	#
	def __init__(self, data_sock):
		threading.Thread.__init__(self)
		self.data_sock = data_sock

	# error handle function
	#
	def sst_error(self, errstr):
		print errstr
		self.data_sock.close()
		exit()	

	# take recv action
	#
	def run(self):
		#
		# if connected, file files to be recved each connection
		#
		file_counter = 5
		while file_counter > 0:
			file_counter = file_counter - 1
			magic_str = ""
			raw_file_name = ""
			file_name = ""
			file_name_len = 0
			file_size = 0
		
			# recv file name len with magic "SHARK"
			#
			magic_str = self.data_sock.recv(8)
			print 'magic_str ' + magic_str
			if magic_str.find("SHARK") != -1:
				file_name_len = string.atol(magic_str[5:]) - 100
				print "file name len: {} ".format(file_name_len)
				if file_name_len == 0:
					self.sst_error('recv file name length failed')
			else:
				self.sst_error('recv file name length failed')
			
			# recv file name 
			#
			raw_file_name = self.data_sock.recv(file_name_len)
			print 'raw file name: ' + raw_file_name
			re_result = re.match(r'[a-zA-Z][._-a-z0-9A-Z]*', raw_file_name)
			if re_result != None and len(re_result.string) != 0:
				file_name = re_result.string
				print "newfs: " + file_name
			else:
				self.sst_error('recv file name failed')
			
			# recv file size with magic "SHARK2"
			#
			magic_str2 = self.data_sock.recv(13)
			print 'magic_str2 ' + magic_str2
			if magic_str2.find("SHARK2") != -1:
				file_size = string.atol(magic_str2[6:]) - 1000000
				print "file size: {} ".format(file_size)
				if file_size == 0:
					self.sst_error('recv file size failed')
			else:
				self.sst_error('recv file size failed')
			
			# create new file ,recv data with results
			# write file
			#
			os.system('mkdir -p /tmp/SHARK/')
			openfile = open('/tmp/SHARK/'+file_name, 'w')
			recved = 0
			while True:
				data = self.data_sock.recv(128)
				recved += len(data)
				#print 'recvlenth {}, recved {}'.format(len(data), recved),
				if recved > file_size:
					extra_cnt = recved - file_size
					end_index = len(data) - extra_cnt
					openfile.write(data[0:end_index])
					print 'someth has been lost'
					break

				#if data == 'EOF':
				#	break
				openfile.write(data)
				if recved == file_size:
					break
			
			openfile.close()

		self.data_sock.close()


# use data socket to recv result files
#
def recv_files(file_cnt):
	listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listen_sock.bind(('',7777))

	recv_cnt = 0
	recv_threads = {}
	while recv_cnt < file_cnt:
		listen_sock.listen(128)
		data_sock,daddr = listen_sock.accept()
		
		recv_threads[recv_cnt] = shark_server_thread(data_sock)
		recv_threads[recv_cnt].start()
		recv_cnt = recv_cnt + 1

		print 'recv cnt {}'.format(recv_cnt)
		#if recv_cnt == file_cnt:
		#	break

	recv_cnt = 0
	while recv_cnt < file_cnt:
		recv_threads[recv_cnt].join()
		recv_cnt = recv_cnt + 1

	listen_sock.close()
	print 'done'

def main():
	idstr = get_idstr()

	client_ip_list = read_conf()
	if client_ip_list == None:
		print 'read conf failed'
		exit()

	client_ip_list.reverse()
	client_ip_list.pop()
	client_ip_tuple = tuple(client_ip_list)

	retry = 10
	send_cnt = 0
	for ip in client_ip_tuple:
		print ip
		ret = send_magic(ip, idstr)
		#print 'sm ret',
		#print ret
		#if ret == -1 and retry > 0:
		#	retry = retry - 1
		#	continue
		#else:
		#		break
		if ret == -1:
			continue 
		else:
			send_cnt = send_cnt + 1
			
	print 'recving files'
	recv_files(send_cnt)

if __name__ == "__main__":
	main()

