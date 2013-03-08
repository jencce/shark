#! /usr/bin/env python
'''SHARK server '''
# 
# execute on any machine, request to SHARK agents to get 
# performance data files 
#
import socket
import os
import re
import threading
import logging
import time

# get requestid string from user to uniq this request
# and so is the cnt and interval param
# for example: sar [interval] [cnt]
# for result file storage
# interactive or read config file
#
def get_idstr():
    ''' get requestid string from user to uniq this request'''

    id_string = raw_input("input 4 chars request idstring:")
    while len(id_string) != 4:
        id_string = raw_input("input 4 chars request idstring:")

    interval_str = raw_input("input count of cmd interval(less then 100):")
    while interval_str.isdigit() != True or int(interval_str) > 100:
        interval_str = raw_input("input count of cmd interval(less then 100):")

    cnt_string = raw_input("input counts of cmd repeat(less then 1000):")
    while cnt_string.isdigit() != True or int(cnt_string) > 1000:
        cnt_string = raw_input("input counts of cmd repeat(less then 1000):")

    cnt_string = repr(int(cnt_string) + 1000)
    interval_str = repr(int(interval_str) + 100)

    return '{0}+{1}+{2}'.format(id_string, cnt_string, interval_str)

# read conf to get clientip list
#
def read_conf():
    ''' read conf to get clientip list'''
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
    '''send passwd and idstr to clients'''
    # set socket timeout to 1 sec
    # if conn failed, client dies, no other action
    #
    try:
        cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cmd_sock.settimeout(1.0)
        cmd_sock.connect((clientip, 7778)) 
        cmd_sock.send("qwe123+"+idstr)
        cmd_sock.close()
    except socket.error as err:
        print err
        logging.error(repr(err))
        return -1


# use data socket to recv result files
#
#def old_recv_files(file_cnt):
#    '''old functionuse data socket to recv result files'''
#    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    listen_sock.bind(('', 7777))
#    listen_sock.listen(5)
#    data_sock, daddr = listen_sock.accept()
#    
#    # if connected, file files to be recved each connection
#    #
#    file_counter = 5
#    while file_counter > 0:
#        file_counter = file_counter - 1
#        raw_file_name = ""
#    
#        # recv file name with magic "SHARK"
#        #
#        raw_file_name = data_sock.recv(100)
#        if raw_file_name.find("SHARK") != -1:
#            file_name = raw_file_name[raw_file_name.find("SHARK")+5:]
#            print "newfs " + file_name
#        else:
#            print "recv filename failed"
#            data_sock.close()
#            exit()
#        
#        # create new file ,recv data with results
#        # write file
#        #
#        os.system('mkdir -p /tmp/SHARK/')
#        openfile = open('/tmp/SHARK/'+file_name, 'w')
#        while True:
#            data = data_sock.recv(1024)
#        #    print 'data: {}, lenth {}'.format(data[0:2], len(data))
#            if data == 'EOF':
#                break
#            openfile.write(data)
#        
#        openfile.close()
#    
#    data_sock.close()
#    print ' done'

# multithread recving files
#
class SharkServerThread(threading.Thread):
    '''multipath recving files
       one thread for each connection'''

    def __init__(self, data_sock):
        '''sst init'''
        threading.Thread.__init__(self)
        self.data_sock = data_sock

    # error handle function
    #
    def sst_error(self, errstr):
        '''handle sst error'''
        print errstr
        logging.error(errstr)
        self.data_sock.close()
        exit()    

    # take recv action
    #
    def run(self):
        '''sst run method'''
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
            logging.info('magic_str ' + magic_str)
            if magic_str.find("SHARK") != -1:
                #file_name_len = string.atol(magic_str[5:]) - 100
                file_name_len = long(magic_str[5:]) - 100
                print "file name len: {} ".format(file_name_len)
                logging.info("file name len: {} ".format(file_name_len))
                if file_name_len == 0:
                    self.sst_error('recv file name length failed')
            else:
                self.sst_error('recv file name length failed')
            
            # recv file name 
            #
            raw_file_name = self.data_sock.recv(file_name_len)
            print 'rawfilename: ' + raw_file_name
            logging.info('rawfilename: ' + raw_file_name)
            re_result = re.match(r'[a-zA-Z][._-a-z0-9A-Z]*', raw_file_name)
            if re_result != None and len(re_result.string) != 0:
                file_name = re_result.string
                print "newfilename: " + file_name
                logging.info("newfilename: " + file_name)
            else:
                self.sst_error('recv file name failed')

            # recv file size with magic "SHARK2"
            #
            magic_str2 = self.data_sock.recv(13)
            print 'magic_str2 ' + magic_str2
            logging.info('magic_str2 ' + magic_str2)
            if magic_str2.find("SHARK2") != -1:
                #file_size = string.atol(magic_str2[6:]) - 1000000
                file_size = long(magic_str2[6:]) - 1000000
                print "file size: {} ".format(file_size)
                logging.info("file size: {} ".format(file_size))
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
                    logging.info('someth has been lost')
                    print 'someth has been lost'
                    break

                #if data == 'EOF':
                #    break
                openfile.write(data)
                if recved == file_size:
                    break
            
            openfile.close()

        self.data_sock.close()

# use data socket to recv result files
#
def recv_files(file_cnt):
    '''server func to recv files
       init a sst thread when connect comes'''
    retry = 10
    while retry > 0:
        try:
            listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_sock.bind(('', 7777))
        except socket.error as err:
            print err,
            print ' :bind failed, retry'
            logging.debug( repr(err) + ':bind failed, retry')
            retry = retry - 1
            time.sleep(1)
            if retry == 0:
                raise
        else:
            break

    recv_cnt = 0
    recv_threads = {}
    while recv_cnt < file_cnt:
        listen_sock.listen(128)
        data_sock, daddr = listen_sock.accept()
        
        recv_threads[recv_cnt] = SharkServerThread(data_sock)
        recv_threads[recv_cnt].start()
        recv_cnt = recv_cnt + 1

        print 'client {} accepted, recvcnt {}'.format(daddr[0], recv_cnt)
        logging.info('client {} accepted, recvcnt {}'.format(daddr[0], \
        recv_cnt))
        #if recv_cnt == file_cnt:
        #    break

    recv_cnt = 0
    while recv_cnt < file_cnt:
        logging.info('waiting recv thread {}'.format(recv_cnt))
        print 'waiting recv thread {}'.format(recv_cnt)
        recv_threads[recv_cnt].join()
        recv_cnt = recv_cnt + 1

    listen_sock.close()
    logging.info("recv files done")
    print 'done'

def main():
    '''shark server main entry'''

    # init log
    log_fmt = '%(process)d: %(asctime)s:%(levelname)s:%(funcName)s: %(message)s'
    log_file = '/home/zx/git/sharkserver.log'
    date_fmt = '%m%d-%H:%M:%S'
    logging.basicConfig(filename=log_file, format=log_fmt, \
    level=logging.DEBUG, datefmt = date_fmt)

    # get idstr
    idstr = get_idstr()

    # read conf file to get ip tuple
    #
    client_ip_list = read_conf()
    if client_ip_list == None:
        logging.error("read conf failed")
        print 'read conf failed'
        exit()

    client_ip_list.reverse()
    client_ip_list.pop()
    client_ip_tuple = tuple(client_ip_list)

    # send magic to shake hands with clients
    #
    send_cnt = 0
    for ip_str in client_ip_tuple:
        print 'sending magic to ' + ip_str
        logging.debug("sending magic to {}".format(ip_str))
        ret = send_magic(ip_str, idstr)
        if ret == -1:
            print "send magic to {} failed".format(ip_str)
            logging.debug("send magic to {} failed".format(ip_str))
            continue 
        else:
            print "send magic to {} succeed".format(ip_str)
            logging.debug("send magic to {} succeed".format(ip_str))
            send_cnt = send_cnt + 1

    # prepare to recv files ahead
    #
    print 'recving files... {}'.format(send_cnt)
    logging.info('recving files... {}'.format(send_cnt))
    recv_files(send_cnt)

if __name__ == "__main__":
    main()

