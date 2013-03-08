#! /usr/bin/env python
'''SHARK agent '''
#
# daemon on target machine, after requestede, execute cmds to
# collect perf data and write to datafile, sending files back 
# to server
#
import socket
import time
import os
from datetime import datetime
import threading
import syslog

# cmd strings needed to execute on client machines
#
#CMD_STRINGS = "sar -n DEV 1 10 > /tmp/sarnDEV-", \
#             "iostat 1 10 > /tmp/iostat-",    \
#             "sar -B 1 10 > /tmp/sarB-",    \
#             "sar -P ALL 1 10 > /tmp/sarPALL-",    \
#             "vmstat 1 10 > /tmp/vmstat-"
CMD_STRINGS = list()

CMD_DKEY = "sar -n DEV", "iostat", "sar -B", "sar -P ALL", "vmstat"

CMD_DVAL = "/tmp/sarnDEV-", "/tmp/iostat-", "/tmp/sarB-", "/tmp/sarPALL-", \
            "/tmp/vmstat-"

CMD_COUNT = 0

CMD_INTERVAL = 0

# shark server addr, get from listen
# shark server addr, get from listen
#
# server_addr = tuple()

# multithreads to run cmds, like sar -P ALL ..
# this is the class to implmt multirhread
#
class SharkClientThread(threading.Thread):
    '''client thread class'''
    cmdstring = ""
    
    def __init__(self, cmdstring):
        threading.Thread.__init__(self)
        self.cmdstring = cmdstring
    
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

# format cmd strings to execute in global var
#
def format_cmd_strings():
    '''assemble the command'''
    global CMD_STRINGS

    CMD_STRINGS = list()
    cmd_dict = dict(zip(CMD_DKEY, CMD_DVAL))
    for cd_key in CMD_DKEY:
        CMD_STRINGS.append('{0} {1} {2} > {3}'.format(cd_key, \
    	repr(CMD_INTERVAL), repr(CMD_COUNT), cmd_dict[cd_key]))

    print CMD_STRINGS

# execute cmds on client machine multithread way
#
def execute_perf_cmds(idstr):
    '''to exec perf cmds'''
    format_cmd_strings()
    sthreads = {}
    for cmds in CMD_STRINGS:
        cmdstring = cmds + idstr
        print 'executing ' + cmdstring
        syslog.syslog(syslog.LOG_DEBUG, 'executing ' + cmdstring)

        sthreads[cmds] = SharkClientThread(cmdstring)
        sthreads[cmds].start()

    for cmds in CMD_STRINGS:
        sthreads[cmds].join()
    print 'end exec cmds'
    syslog.syslog(syslog.LOG_DEBUG, 'exec cmds end')

# listen socket to accept cmd connection where get passwd 
# and requestid.  if connection accepted, end blocking
#
def get_idstr():
    '''get idstr func'''
    #os.system('hostname > /tmp/hn')
    #hnfile = open('/tmp/hn')
    #host_name = string.rstrip(hnfile.readline(), '\n')
    host_name = os.popen('hostname').readline().rstrip('\n')
    #hnfile.close()

    dtstr = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')

    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.bind(('', 7778))
    listen_sock.listen(5)
    cmd_sock, cmd_addr = listen_sock.accept()
    #print 'cmdaddr',
    #print cmd_addr
    server_addr = cmd_addr[0]
    
    # handshake to verify passwd 
    # cmd socket to get cmd string
    #
    while True:
        cmdstr = cmd_sock.recv(20)
        if cmdstr[0:6] == 'qwe123':
            break
    
    cmd_sock.close()
    listen_sock.close()

    print 'recved idstr: {0} from {1}'.format(cmdstr, server_addr)
    syslog.syslog(syslog.LOG_DEBUG, 'recved idstr: {0} from {1}'.format(\
    cmdstr, server_addr))

    tmp_list = cmdstr.split('+')
    if len(tmp_list) != 4:
        print 'recved idstring error'
        syslog.syslog(syslog.LOG_DEBUG, 'recved idstr error')
        exit()

    idstr = tmp_list[1] + '-' + host_name + '-' + dtstr 
    global CMD_COUNT
    global CMD_INTERVAL
    CMD_COUNT = int(tmp_list[2]) - 1000
    CMD_INTERVAL = int(tmp_list[3]) - 100
    #idstr = cmdstr[cmdstr.find("+")+1:] + '-' + host_name + '-' + dtstr 
    rt_t = (idstr, server_addr)
    return rt_t


# handle send_files error
#
def sf_error(errstr, data_sock):
    '''handle send file error'''
    print errstr
    syslog.syslog(syslog.LOG_DEBUG, errstr)
    data_sock.close()
    exit()

# connect to server to send files
#
def send_files(idstr_sd_t):
    '''send files to server'''
    # use magic coming addr
    #
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print 'send_files beagin idstr: ' + idstr_sd_t[0] + 'server ip: ' + \
    idstr_sd_t[1]
    syslog.syslog(syslog.LOG_DEBUG, 'send_files beagin idstr: ' + \
    idstr_sd_t[0] + 'server ip: ' + idstr_sd_t[1])
    retry = 10
    while retry > 0:
        try:
            data_sock.connect((idstr_sd_t[1], 7777)) 
        except socket.error as err:
            print err,
            print 'conn to server failed, retry'
            syslog.syslog(syslog.LOG_DEBUG, repr(err))
            syslog.syslog(syslog.LOG_DEBUG, 'conn to sver fail, retry')
            retry = retry - 1
            time.sleep(2)
            if retry == 0:
                raise
        else:
            break

    
    # five files to transfer
    #
    for css in CMD_STRINGS:
        cmds = css + idstr_sd_t[0]
        # get file name and size, check
        #
        file_name = cmds[cmds.find("/tmp")+5:]

        file_size = 0
        stat_rt = os.stat(cmds[cmds.find("/tmp"):])
        if stat_rt != None and stat_rt.st_size != 0:
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
        #print 'magic2 ' + string.rstrip(magic_str2, 'L')
        print 'magic2 ' + magic_str2.rstrip('L')
        syslog.syslog(syslog.LOG_DEBUG, 'magic2 ' + magic_str2.rstrip('L'))
        sended = data_sock.send(magic_str2.rstrip('L'))
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
    '''main func'''
    while True:
        get_t = []
        get_t = get_idstr()
        if len(get_t[0]) <= 0:
            syslog.syslog(syslog.LOG_DEBUG, "get idstr failed")
            print 'get idstr failed'
            exit()

        # execute cmds and send files
        execute_perf_cmds(get_t[0])
        time.sleep(5)
    
        # send cmd-result files to server
        send_files(get_t)

        # touch SK to exit, prply not work
        #stat_rt = os.stat('/tmp/SK')
        #if stat_rt != None:
        #    syslog.syslog(syslog.LOG_DEBUG, "SK exited")
        #    break

if __name__ == '__main__':
    syslog.openlog("SHARK", syslog.LOG_NDELAY, syslog.LOG_USER)
    main()
    syslog.closelog()
