#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# @Time    : 2019-10-16
# @Author  : lework
# @Desc    : 一个事件监听器，订阅PROCESS_STATE_CHANGE事件。当supervisor管理的进程意外过渡到EXITED状态时，它将发送邮件。

# [eventlistener:supervisor_event_exited]
# process_name=%(program_name)s
# command=/usr/bin/python /data/scripts/supervisor_event_exited.py
# autostart=true
# autorestart=true
# events=PROCESS_STATE
# log_stdout=true
# log_stderr=true
# stdout_logfile=/var/log/supervisor/supervisor_event_exited-stdout.log
# stdout_logfile_maxbytes=50MB
# stdout_logfile_backups=3
# buffer_size=10
# stderr_logfile=/var/log/supervisor/supervisor_event_exited-stderr.log
# stderr_logfile_maxbytes=50MB
# stderr_logfile_backups=3


import os
import smtplib
import socket
import sys
from supervisor import childutils
from email.header import Header
from email.mime.text import MIMEText


class CrashMail:
    def __init__(self, mail_config, programs):
        self.mail_config = mail_config
        self.programs = programs
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.time = ''

    def write_stderr(self, s):
        s = s+'\n'
	if self.time:
           s = '[%s] %s' % (self.time, s)
        self.stderr.write(s)
        self.stderr.flush()

    def runforever(self):
        # 死循环, 处理完 event 不退出继续处理下一个
        while 1:
            # 使用 self.stdin, self.stdout, self.stderr 代替 sys.*
            headers, payload = childutils.listener.wait(self.stdin, self.stdout)

            self.time = childutils.get_asctime()
            self.write_stderr('[headers] %s' % str(headers))
            self.write_stderr('[payload] %s' % str(payload))

            # 不处理不是 PROCESS_STATE_EXITED 类型的 event, 直接向 stdout 写入"RESULT\nOK"
            if headers['eventname'] != 'PROCESS_STATE_EXITED':
                childutils.listener.ok(self.stdout)
                continue

            # 解析 payload, 这里我们只用这个 pheaders.
            # pdata 在 PROCESS_LOG_STDERR 和 PROCESS_COMMUNICATION_STDOUT 等类型的 event 中才有
            pheaders, pdata = childutils.eventdata(payload + '\n')

            # 如果在programs中设置，就只处理programs中的，否则全部处理.
            if len(self.programs) !=0 and pheaders['groupname'] not in self.programs:
                childutils.listener.ok(self.stdout)
	        continue

            # 过滤掉 expected 的 event, 仅处理 unexpected 的
            # 当 program 的退出码为对应配置中的 exitcodes 值时, expected=1; 否则为0
            if int(pheaders['expected']):
                childutils.listener.ok(self.stdout)
                continue

            # 获取系统主机名和ip地址
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)

            # 构造报警内容
            msg = "Host: %s(%s)\nProcess: %s\nPID: %s\nEXITED unexpectedly from state: %s" % \
                  (hostname, ip, pheaders['processname'], pheaders['pid'], pheaders['from_state'])

            subject = '[Supervistord] %s crashed at %s' % (pheaders['processname'], self.time)

            self.write_stderr('[INFO] unexpected exit, mailing')

            # 发送邮件
            self.send_mail(subject, msg)

            # 向 stdout 写入"RESULT\nOK"，并进入下一次循环
            childutils.listener.ok(self.stdout)

    def send_mail(self, subject, content):
        """
        :param subject: str
        :param content: str
        :return: bool
        """

        mail_port = self.mail_config.get('mail_port', '')
        mail_host = self.mail_config.get('mail_host', '')
        mail_user = self.mail_config.get('mail_user', '')
        mail_pass = self.mail_config.get('mail_pass', '')
        to_list = self.mail_config.get('to_list', [])

        msg = MIMEText(content, _subtype='plain', _charset='utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = mail_user
        msg['to'] = ",".join(to_list)
        try:
            s = smtplib.SMTP_SSL(mail_host, mail_port)
            s.login(mail_user, mail_pass)
            s.sendmail(mail_user, to_list, msg.as_string())
            s.quit()
            self.write_stderr('[mail] ok')
            return True
        except Exception as e:
            self.write_stderr('[mail] error\n\n%s\n' % e)
            return False


def main():
    # listener 必须交由 supervisor 管理, 直接运行是不行的
    if not 'SUPERVISOR_SERVER_URL' in os.environ:
        sys.stderr.write('crashmail must be run as a supervisor event '
                         'listener\n')
        sys.stderr.flush()
        return

    # 设置smtp信息
    mail_config = {
        'mail_host': 'smtp.lework.com',
        'mail_port': '465',
        'mail_user': 'ops@lework.com',
        'mail_pass': '123123123',
        'to_list': ['lework@lework.com']
    }

    # 设置要检测的program,不设置则检测全部
    programs = []
    prog = CrashMail(mail_config, programs)
    prog.runforever()


if __name__ == '__main__':
    main()
