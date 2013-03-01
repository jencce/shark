#! /usr/bin/env python
# SHARK server 
#
# execute on any machine, request to SHARK agents to get
# performance data files 
#
import socket
import time
import os

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
		if find_clientip != -1:
			client_ip_list = conf_item.split()
			return client_ip_list


# cmdsocket to shake hands with clients
# predef string as passwd
# passwd and requestid string as magic words
#
def send_magic(clientip, idstr):
	cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	cmd_sock.connect((clientip,7778)) # TOD if conn failed returen smth
	cmd_sock.send("qwe123+"+idstr)
	cmd_sock.close()


# use data socket to recv result files
#
def recv_files(clientip):
	data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	data_sock.connect((clientip,7777))
	
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
			if data == 'EOF':
				break
			openfile.write(data)
		
		openfile.close()
	
	data_sock.close()
	print client_ip + ' done'


if __name__ == "__main__":

	idstr = get_idstr()

	client_ip_list = read_conf()
	if client_ip_list == None:
		print 'read conf failed'
		exit()

	client_ip_list.reverse()
	client_ip_list.pop()
	print client_ip_list

	while client_ip_list.__len__():
		client_ip = client_ip_list.pop() 
		print client_ip
		send_magic(client_ip, idstr)  #check return
		time.sleep(2)
		recv_files(client_ip)

