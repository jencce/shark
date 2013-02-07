#! /usr/bin/env python
import socket
import time


idstring = raw_input("input 4 charactors request idstring:")
while len(idstring) != 4:
	idstring = raw_input("input 4 charactors request idstring:")
	
config_file = open("shark.conf")
for conf_item in config_file:
	print conf_item,
	find_clientip = conf_item.find("clientip")
	if find_clientip != -1:
		client_ip_list = conf_item.split()


cmdsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cmdsock.connect(('127.0.0.1',7778))
cmdsock.send("qwe123+"+idstring)
cmdsock.close()

time.sleep(2)

datasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
datasock.connect((clientip,7777))

file_counter = 5
while file_counter > 0:
	file_counter = file_counter - 1
	raw_file_name = ""
	raw_file_name = datasock.recv(48)
	print raw_file_name
	if raw_file_name.find("SHARK") != -1:
		file_name = raw_file_name[raw_file_name.find("SHARK")+5:]
		print "newfs " + file_name
	else:
		print "recv filename failed"
		datasock.close()
		exit()
	
	openfile = open("/tmp"+file_name, 'w')
	while True:
		data = datasock.recv(1024)
		if data == 'EOF':
			break
		openfile.write(data)
	
	openfile.close()

datasock.close()
print 'done'
