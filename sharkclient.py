#! /usr/bin/env python
import socket
import time

cmdsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cmdsock.bind(('',7778))
cmdsock.listen(5)
cs,caddr = cmdsock.accept()
while True:
	cmdstr = cs.recv(100)
	if cmdstr[0:6] == 'qwe123':
		break
	time.sleep(2)

print cmdstr

sersock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sersock.bind(('',7777))
sersock.listen(5)
ds,daddr = sersock.accept()

fn = open('/tmp/sar')
while True:
	data = fn.read(1024)
	if not data:
		break
	while len(data) > 0:
		sended = ds.send(data)
		data = data[sended:]

time.sleep(2)
ds.send('EOF')
fn.close()


print daddr
ds.close()
