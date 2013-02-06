#! /usr/bin/env python
import socket

idstring = raw_input("input 4 charactors request idstring:")
while len(idstring) != 4:
	idstring = raw_input("input 4 charactors request idstring:")
	

cmdsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cmdsock.connect(('127.0.0.1',7778))
cmdsock.send("qwe123+"+idstring)
cmdsock.close()

cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cs.connect(('127.0.0.1',7777))

fn = open('sar', 'w')
while True:
	data = cs.recv(1024)
	if data == 'EOF':
		break
	fn.write(data)

fn.close()
print 'done'

