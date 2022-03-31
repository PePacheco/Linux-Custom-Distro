import time
import datetime
import platform
import os
import subprocess

from http.server import BaseHTTPRequestHandler, HTTPServer


HOST_NAME = '0.0.0.0' # 0.0.0.0
PORT_NUMBER = 8000

def get_pname(id):
        p = subprocess.Popen(["ps -o cmd= {}".format(id)], stdout=subprocess.PIPE, shell=True)
        return str(p.communicate()[0])

class GetCpuLoad(object):
    '''
    classdocs
    '''


    def __init__(self, percentage=True, sleeptime = 1):
        '''
        @parent class: GetCpuLoad
        @date: 04.12.2014
        @author: plagtag
        @info: 
        @param:
        @return: CPU load in percentage
        '''
        self.percentage = percentage
        self.cpustat = '/proc/stat'
        self.cpuinfo = '/proc/cpuinfo'
        self.meminfo = '/proc/meminfo'
        self.sep = ' ' 
        self.sleeptime = sleeptime

    def getcputime(self):
        '''
        http://stackoverflow.com/questions/23367857/accurate-calculation-of-cpu-usage-given-in-percentage-in-linux
        read in cpu information from file
        The meanings of the columns are as follows, from left to right:
            0cpuid: number of cpu
            1user: normal processes executing in user mode
            2nice: niced processes executing in user mode
            3system: processes executing in kernel mode
            4idle: twiddling thumbs
            5iowait: waiting for I/O to complete
            6irq: servicing interrupts
            7softirq: servicing softirqs

        #the formulas from htop 
             user    nice   system  idle      iowait irq   softirq  steal  guest  guest_nice
        cpu  74608   2520   24433   1117073   6176   4054  0        0      0      0


        Idle=idle+iowait
        NonIdle=user+nice+system+irq+softirq+steal
        Total=Idle+NonIdle # first line of file for all cpus

        CPU_Percentage=((Total-PrevTotal)-(Idle-PrevIdle))/(Total-PrevTotal)
        '''
        cpu_infos = {} #collect here the information
        with open(self.cpustat,'r') as f_stat:
            lines = [line.split(self.sep) for content in f_stat.readlines() for line in content.split('\n') if line.startswith('cpu')]

            #compute for every cpu
            for cpu_line in lines:
                if '' in cpu_line: cpu_line.remove('')#remove empty elements
                cpu_line = [cpu_line[0]]+[float(i) for i in cpu_line[1:]]#type casting
                cpu_id,user,nice,system,idle,iowait,irq,softrig,steal,guest,guest_nice = cpu_line

                Idle=idle+iowait
                NonIdle=user+nice+system+irq+softrig+steal

                Total=Idle+NonIdle
                #update dictionionary
                cpu_infos.update({cpu_id:{'total':Total,'idle':Idle}})
            return cpu_infos

    def getcpuinfo(self):
        cpu_infos = {} #collect here the information
        with open(self.cpuinfo,'r') as f_info:
            content = f_info.readlines()
            return content[4]

    def getprocesses(self):
        pids = [int(x) for x in os.listdir('/proc') if x.isdigit()]
        return pids

    def getcpuload(self):
        '''
        CPU_Percentage=((Total-PrevTotal)-(Idle-PrevIdle))/(Total-PrevTotal)

        '''
        start = self.getcputime()
        #wait a second
        time.sleep(1)
        stop = self.getcputime()

        cpu_load = {}

        for cpu in start:
            Total = stop[cpu]['total']
            PrevTotal = start[cpu]['total']

            Idle = stop[cpu]['idle']
            PrevIdle = start[cpu]['idle']
            CPU_Percentage=((Total-PrevTotal)-(Idle-PrevIdle))/(Total-PrevTotal)*100
            cpu_load.update({cpu: CPU_Percentage})
        return cpu_load

    def getramusage(self):
        with open(self.meminfo,'r') as f_meminfo:
            content = f_meminfo.readlines()
            memTotal = int(content[0][17:-4])
            memUsed = int(content[1][16:-4])

            return (memUsed/memTotal)*100            

class MyHandler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
    def do_GET(self):
        x = GetCpuLoad()
        """Respond to a GET request."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><head><title>Title goes here.</title></head>")
        self.wfile.write(b"<body><p>This is a test.</p>")
        # If someone went to "http://something.somewhere.net/foo/bar/",
        # then s.path equals "/foo/bar/".
        pathVersion = "<p>Your platform: {}</p>".format(platform.platform())
        self.wfile.write(pathVersion.encode())
        pathProc = "<p>{}</p>".format(x.getcpuinfo())
        self.wfile.write(pathProc.encode())
        pathCpuUptime = "<p>CPU uptime: {}</p>".format(x.getcputime())
        self.wfile.write(pathCpuUptime.encode())
        pathCpu = "<p>Your CPU usage: {}</p>".format(x.getcpuload())
        self.wfile.write(pathCpu.encode())
        pathRAM = "<p>Your RAM usage: {}%</p>".format(x.getramusage())
        self.wfile.write(pathRAM.encode())
        pathDatetime = "<p>Datetime: {}</p>".format(datetime.datetime.now())
        self.wfile.write(pathDatetime.encode())
        pathProcecess = "<p>Procecess:</>"
        self.wfile.write(pathProcecess.encode())
        x.getprocesses()
        self.wfile.write(b"<li>")
        for proc in x.getprocesses():
            listProcess = "<ul>{} - {}</ul>".format(proc, get_pname(proc))
            self.wfile.write(listProcess.encode())
        self.wfile.write(b"</li>")
        self.wfile.write(b"</body></html>")

if __name__ == '__main__':

    server_class = HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print(time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))

