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
def getidstr():
	idstring = raw_input("input 4 chars request idstring:")
	while len(idstring) != 4:
		idstring = raw_input("input 4 chars request idstring:")
	return idstring

# read conf to get clientip list
#
def readconf():
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
def sendmagic(clientip, idstr):
	cmdsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	cmdsock.connect((clientip,7778)) # TOD
	cmdsock.send("qwe123+"+idstr)
	cmdsock.close()



# use data socket to recv result files
#
def recvfiles(clientip):
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
		raw_file_name = datasock.recv(100)
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
		os.system('mkdir -p /tmp/SHARK/')
		openfile = open('/tmp/SHARK/'+file_name, 'w')
		while True:
			data = datasock.recv(1024)
			if data == 'EOF':
				break
			openfile.write(data)
		
		openfile.close()
	
	datasock.close()
	print client_ip + ' done'


if __name__ == "__main__":

	idstr = getidstr()

	client_ip_list = readconf()
	if client_ip_list == None:
		print 'read conf failed'
		exit()

	client_ip_list.reverse()
	client_ip_list.pop()
	print client_ip_list

	while client_ip_list.__len__():
		client_ip = client_ip_list.pop() 
		sendmagic(client_ip, idstr)
		time.sleep(2)
		recvfiles(client_ip)

