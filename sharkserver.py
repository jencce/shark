#! /usr/bin/env python
# SHARK server 
#
# execute on any machine, request to SHARK agents to get
# performance data files 
#
import socket
import time

# get requestid string from user to uniq this request
# for result file storage
# interactive or read config file

idstring = raw_input("input 4 charactors request idstring:")
while len(idstring) != 4:
	idstring = raw_input("input 4 charactors request idstring:")
	
config_file = open("shark.conf")
for conf_item in config_file:
	print conf_item,
	find_clientip = conf_item.find("clientip")
	if find_clientip != -1:
		client_ip_list = conf_item.split()


# cmdsocket to shake hands with clients
# predef string as passwd
# passwd andrequestid string as magic words

cmdsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cmdsock.connect(('127.0.0.1',7778)) # TOD
cmdsock.send("qwe123+"+idstring)
cmdsock.close()

time.sleep(2)

# use data socket to recv result files

datasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
datasock.connect((clientip,7777))

# if connected, file files to be recved each connection
#
file_counter = 5
while file_counter > 0:
	file_counter = file_counter - 1
	raw_file_name = ""

	# recv file name with magic "SHARK"
	#
	raw_file_name = datasock.recv(48)
	print raw_file_name
	if raw_file_name.find("SHARK") != -1:
		file_name = raw_file_name[raw_file_name.find("SHARK")+5:]
		print "newfs " + file_name
	else:
		print "recv filename failed"
		datasock.close()
		exit()
	
	# create new file ,recv data with results
	# write file
	#
	openfile = open("/tmp"+file_name, 'w')
	while True:
		data = datasock.recv(1024)
		if data == 'EOF':
			break
		openfile.write(data)
	
	openfile.close()

datasock.close()
print 'done'
