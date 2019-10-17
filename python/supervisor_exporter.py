#!/usr/bin/python
# -*- coding: utf-8 -*-

# @Time    : 2019-10-15
# @Author  : lework
# @Desc    : 收集supervisor的进程状态信息，并将信息暴露给Prometheus。

# [program:supervisor_exporter]
# process_name=%(program_name)s
# command=/usr/bin/python /root/scripts/supervisor_exporter.py
# autostart=true
# autorestart=true
# redirect_stderr=true
# stdout_logfile=/var/log/supervisor/supervisor_exporter.log
# stdout_logfile_maxbytes=50MB
# stdout_logfile_backups=3
# buffer_size=10


from xmlrpclib import ServerProxy
from prometheus_client import Gauge, Counter, CollectorRegistry ,generate_latest, start_http_server
from time import sleep

try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    # Python 3
    from http.server import BaseHTTPRequestHandler, HTTPServer

def is_runing(state):
    state_info = {
            # 'STOPPED': 0,
            'STARTING': 10,
            'RUNNING': 20
            # 'BACKOFF': 30,
            # 'STOPPING': 40
            # 'EXITED': 100,
            # 'FATAL': 200,
            # 'UNKNOWN': 1000
    }
    if state in state_info.values():
        return True
    return  False


def get_metrics():
    collect_reg = CollectorRegistry(auto_describe=True)

    try:
        s = ServerProxy(supervisord_url)
        data = s.supervisor.getAllProcessInfo()
    except Exception as e:
        print("unable to call supervisord: %s" % e)
        return collect_reg

    labels=('name', 'group')

    metric_state = Gauge('state', "Process State", labelnames=labels, subsystem='supervisord', registry=collect_reg)
    metric_exit_status=Gauge('exit_status', "Process Exit Status", labelnames=labels, subsystem='supervisord', registry=collect_reg)
    metric_up = Gauge('up', "Process Up", labelnames=labels, subsystem='supervisord', registry=collect_reg)
    metric_start_time_seconds=Counter('start_time_seconds', "Process start time", labelnames=labels, subsystem='supervisord', registry=collect_reg)

    for item in data:
        now = item.get('now', '')
        group = item.get('group', '')
        description = item.get('description', '')
        stderr_logfile = item.get('stderr_logfile', '')
        stop = item.get('stop', '')
        statename = item.get('statename', '')
        start = item.get('start', '')
        state = item.get('state', '')
        stdout_logfile = item.get('stdout_logfile', '')
        logfile = item.get('logfile', '')
        spawnerr = item.get('spawnerr', '')
        name = item.get('name', '')
        exitstatus = item.get('exitstatus', '')

        labels = (name, group)

        metric_state.labels(*labels).set(state)
        metric_exit_status.labels(*labels).set(exitstatus)

        if is_runing(state):
            metric_up.labels(*labels).set(1)
	    metric_start_time_seconds.labels(*labels).inc(start)
        else:
            metric_up.labels(*labels).set(0)

    return  collect_reg


class myHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        data=""
        if self.path=="/":
            data="hello, supervistor."
	elif self.path=="/metrics":
            data=generate_latest(get_metrics())
        else:
            data="not found"
	    # Send the html message
        self.wfile.write(data)
        return

if __name__ == '__main__':
    try:
        supervisord_url = "http://localhost:9001/RPC2"
		
        PORT_NUMBER = 8000
        #Create a web server and define the handler to manage the
        #incoming request
        server = HTTPServer(('', PORT_NUMBER), myHandler)
        print 'Started httpserver on port ' , PORT_NUMBER
	
        #Wait forever for incoming htto requests
        server.serve_forever()

    except KeyboardInterrupt:
        print '^C received, shutting down the web server'
        server.socket.close()
    
