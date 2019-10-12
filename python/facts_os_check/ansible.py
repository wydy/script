#!/usr/bin/python
# -*- coding: utf-8 -*-

# @Time    : 2019-10-09
# @Author  : lework


import datetime
import smtplib
import os
import json
import codecs
import copy
from email.header import Header
from email.mime.text import MIMEText
import urllib.request
from jinja2 import FileSystemLoader, Environment


def deepupdate(target, src, overwrite=True):
    """Deep update target list, dict or set or other iterable with src
    For each k,v in src: if k doesn't exist in target, it is deep copied from
    src to target. Otherwise, if v is a list, target[k] is extended with
    src[k]. If v is a set, target[k] is updated with v, If v is a dict,
    recursively deep-update it. If `overwrite` is False, existing values in
    target will not be overwritten.
    Examples:
    \>>> t = {'name': 'Ferry', 'hobbies': ['programming', 'sci-fi']}
    \>>> deepupdate(t, {'hobbies': ['gaming']})
    \>>> print t
    {'name': 'Ferry', 'hobbies': ['programming', 'sci-fi', 'gaming']}
    """
    for k, v in src.items():
        if type(v) == list:
            if not k in target:
                target[k] = copy.deepcopy(v)
            elif overwrite is True:
                target[k].extend(v)
        elif type(v) == dict:
            if not k in target:
                target[k] = copy.deepcopy(v)
            else:
                deepupdate(target[k], v, overwrite=overwrite)
        elif type(v) == set:
            if not k in target:
                target[k] = v.copy()
            elif overwrite is True:
                if type(target[k]) == list:
                    target[k].extend(v)
                elif type(target[k]) == set:
                    target[k].update(v)
                else:
                    raise TypeError("Cannot update {} with {}".format(type(target[k]), type(v)))
        else:
            if k not in target or overwrite is True:
                target[k] = copy.copy(v)


def send_mail(mail_config, to_list, subject, content):
    """
    发送HTML类型的邮件
    :param mail_config: dict
    :param to_list: list
    :param subject: str
    :param content: str
    :return:
    """

    mail_port = mail_config.get('mail_port', '')
    mail_host = mail_config.get('mail_host', '')
    mail_user = mail_config.get('mail_user', '')
    mail_pass = mail_config.get('mail_pass', '')

    me = mail_user
    msg = MIMEText(content, _subtype='html', _charset='utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = me
    msg['to'] = ",".join(to_list)
    try:
        s = smtplib.SMTP_SSL(mail_host, mail_port)
        s.login(mail_user, mail_pass)
        s.sendmail(me, to_list, msg.as_string())
        s.quit()
        print("[Send mail] success.")
        return True
    except Exception as e:
        print("[Send mail] error. %s" % e)
        return False


class Ansible(object):
    """
    生成主机信息
    """

    def __init__(self, fact_dirs, fact_cache=False):

        self.fact_dirs = fact_dirs
        self.fact_cache = fact_cache
        self.host_data = {}
        self.remote_timestamp = 0

        # 条件
        self.bad_threshold = 80
        self.critical_threshold = 90
        self.time_threshold = 10 * 60

        self.default_host_info = [
            'ansible_hostname',
            'ansible_default_ipv4',
            'ansible_distribution',
            'ansible_distribution_version',
            'ansible_kernel',
            'ansible_dns',
            'ansible_uptime_seconds',
            'ansible_date_time',
            'ansible_memory_mb',
            'ansible_memfree_mb',
            'ansible_memtotal_mb',
            'ansible_mounts',
            'ansible_swaptotal_mb',
            'ansible_swapfree_mb'
        ]

        self.check_result = {
            'time': '',
            'summary': {
                'ok': 0,
                'bad': 0,
                'critical': 0,
                'total': 0,
                'error': 0
            },
            'ok': [],
            'bad': [],
            'critical': [],
            'ok_item': {},
            'bad_item': {},
            'critical_item': {},
            'error_item': {}
        }

        for fact_dir in self.fact_dirs:
            self._parse_fact_dir(fact_dir, self.fact_cache)

        self._set_remote_timestamp()

    def _parse_fact_dir(self, fact_dir, fact_cache=False):
        if not os.path.isdir(fact_dir):
            raise IOError("Not a directory: '{0}'".format(fact_dir))

        flist = []
        for (dirpath, dirnames, filenames) in os.walk(fact_dir):
            flist.extend(filenames)
            break

        for fname in flist:
            if fname.startswith('.'):
                continue
            hostname = fname

            fd = codecs.open(os.path.join(fact_dir, fname), 'r', encoding='utf8')
            s = fd.readlines()
            fd.close()
            try:
                x = json.loads(''.join(s))
                # for compatibility with fact_caching=jsonfile
                # which omits the "ansible_facts" parent key added by the setup module
                if self.fact_cache:
                    x = json.loads('{ "ansible_facts": ' + ''.join(s) + ' }')
                self.update_host(hostname, x)
                self.update_host(hostname, {'name': hostname})
            except ValueError as e:
                # Ignore non-JSON files (and bonus errors)
                print("Error parsing: %s: %s" % (fname, e))

    def _set_remote_timestamp(self):
        time_api = "http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp"
        try:
            response = urllib.request.urlopen(time_api)
            result = json.loads(response.read().decode('utf-8'))
            self.remote_timestamp = int(result['data'].get('t', '0'))
        except Exception as e:
            self.remote_timestamp = datetime.datetime.timestamp(datetime.datetime.now())

    def check_time(self, host, item, now):
        now_timestamp = datetime.datetime.timestamp(datetime.datetime.strptime(now, "%Y-%m-%dT%H:%M:%SZ"))
        time_zone = 8 * 60 * 60

        if abs(self.remote_timestamp - now_timestamp - time_zone) >= self.time_threshold:
            self.check_result['critical'].append(host)
            if host not in self.check_result['critical_item']:
                self.check_result['critical_item'][host] = {'critical': [], 'bad': []}
            self.check_result['critical_item'][host]['critical'].append(item)

    def check_usedutilization(self, host, item, now):
        if now >= self.critical_threshold:
            self.check_result['critical'].append(host)
            if host not in self.check_result['critical_item']:
                self.check_result['critical_item'][host] = {'critical': [], 'bad': []}
            self.check_result['critical_item'][host]['critical'].append(item)

        elif now >= self.bad_threshold:
            if host in self.check_result['critical']:
                self.check_result['critical_item'][host]['bad'].append(item)
                return
            self.check_result['bad'].append(host)
            if host not in self.check_result['bad_item']:
                self.check_result['bad_item'][host] = {'bad': []}
            self.check_result['bad_item'][host]['bad'].append(item)
        else:
            if host in self.check_result['critical'] or host in self.check_result['bad']:
                return
            self.check_result['ok'].append(host)

    def update_host(self, hostname, key_values, overwrite=True):
        """
        Update a hosts information. This is called by various collectors such
        as the ansible setup module output and the hosts parser to add
        informatio to a host. It does some deep inspection to make sure nested
        information can be updated.
        """
        default_empty_host = {
            'name': hostname,
        }
        host_info = self.host_data.get(hostname, default_empty_host)
        deepupdate(host_info, key_values, overwrite=overwrite)
        self.host_data[hostname] = host_info

    def get_check_result(self):
        for key, host in self.host_data.items():
            print('[Check] %s' % key)
            if 'ansible_facts' not in host:
                self.check_result['summary']['error'] += 1
                self.check_result['error_item'][key] = {'msg': host['msg']}
                continue

            usedutilization = {
                'os_time': '',
                'mem': '',
                'swap': '',
                'disk': []
            }

            iso8601 = host['ansible_facts']['ansible_date_time'].get('iso8601', None)
            ansible_memtotal_mb = host['ansible_facts'].get('ansible_memtotal_mb', 0)
            ansible_memfree_mb = host['ansible_facts'].get('ansible_memfree_mb', 0)
            ansible_swaptotal_mb = host['ansible_facts'].get('ansible_swaptotal_mb', 0)
            ansible_swapfree_mb = host['ansible_facts'].get('ansible_swapfree_mb', 0)

            if ansible_memtotal_mb != 0:
                usedutilization['mem'] = int(
                    (ansible_memtotal_mb - ansible_memfree_mb) / ansible_memtotal_mb * 10000) / 100
            else:
                usedutilization['mem'] = 0

            if ansible_swaptotal_mb != 0:
                usedutilization['swap'] = int(
                    (ansible_swaptotal_mb - ansible_swapfree_mb) / ansible_swaptotal_mb * 10000) / 100
            else:
                usedutilization['swap'] = 0

            usedutilization['os_time'] = iso8601

            for disk in host['ansible_facts'].get('ansible_mounts', []):
                mount = disk.get('mount', '')
                fstype = disk.get('fstype', '')
                if 'containers' in mount or 'iso9660' in fstype:
                    continue
                size_total = disk.get('size_total', 0)
                size_available = disk.get('size_available', 0)
                block_used = disk.get('block_used', 0)
                block_total = disk.get('block_total', 0)
                inode_total = disk.get('inode_total', 0)
                inode_used = disk.get('inode_used', 0)

                size_usedutilization = 0
                block_usedutilization = 0
                inode_usedutilization = 0

                if size_total != 0:
                    size_usedutilization = int((size_total - size_available) / size_total * 10000) / 100

                if block_total != 0:
                    block_usedutilization = int(block_used / block_total * 10000) / 100

                if inode_total != 0:
                    inode_usedutilization = int(inode_used / inode_total * 10000) / 100

                usedutilization['disk'].append(
                    {'mount': mount, 'size': size_usedutilization, 'block': block_usedutilization,
                     'inode': inode_usedutilization})

            self.check_usedutilization(key, 'mem', usedutilization['mem'])
            self.check_usedutilization(key, 'swap', usedutilization['swap'])

            for du in usedutilization['disk']:
                self.check_usedutilization(key, 'mount_size_' + mount, du['size'])
                self.check_usedutilization(key, 'mount_block_' + mount, du['block'])
                self.check_usedutilization(key, 'mount_inode_' + mount, du['inode'])

            # self.check_time(key, 'time', iso8601)
            self.host_data[key]['usedutilization'] = usedutilization

        self.check_result['ok'] = sorted(
            list(set(self.check_result['ok']).difference(set(self.check_result['critical']))))
        self.check_result['ok'] = sorted(list(set(self.check_result['ok']).difference(set(self.check_result['bad']))))
        self.check_result['bad'] = sorted(
            list(set(self.check_result['bad']).difference(set(self.check_result['critical']))))
        self.check_result['critical'] = sorted(set(self.check_result['critical']))
        self.check_result['total'] = len(self.host_data.values())

        self.check_result['summary']['ok'] = len(self.check_result['ok'])
        self.check_result['summary']['bad'] = len(self.check_result['bad'])
        self.check_result['summary']['critical'] = len(self.check_result['critical'])
        self.check_result['summary']['total'] = len(self.host_data.values())

        self.check_result['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for ok_item in self.check_result['ok']:
            self.check_result['ok_item'][ok_item] = {}
            for info in self.default_host_info:
                self.check_result['ok_item'][ok_item][info] = self.host_data[ok_item]['ansible_facts'][info]
            self.check_result['ok_item'][ok_item]['usedutilization'] = self.host_data[ok_item]['usedutilization']

        for bad_item in self.check_result['bad']:
            for info in self.default_host_info:
                self.check_result['bad_item'][bad_item][info] = self.host_data[bad_item]['ansible_facts'][info]
            self.check_result['bad_item'][bad_item]['usedutilization'] = self.host_data[bad_item]['usedutilization']

        for critical_item in self.check_result['critical']:
            for info in self.default_host_info:
                self.check_result['critical_item'][critical_item][info] = \
                    self.host_data[critical_item]['ansible_facts'][
                        info]
            self.check_result['critical_item'][critical_item]['usedutilization'] = self.host_data[critical_item][
                'usedutilization']

        return self.check_result


if __name__ == '__main__':
    # 定义基础数据
    print('[Init] Set configuration')
    current_path = os.path.dirname(os.path.abspath(__file__))
    now_date = datetime.datetime.now().strftime('%Y-%m-%d')
    report_path = os.path.join(current_path, 'report', 'report-%s.html' % now_date)
    template_path = os.path.join(current_path, 'templates')
    # template_file = 'report.html'
    template_file = 'report_cssinline.html'

    # 设置fact目录
    fact_dirs = [os.path.join(current_path, 'facts')]

    # 获取检查结果
    print('[Check] Get Result')
    ansible = Ansible(fact_dirs=fact_dirs)
    check_result = ansible.get_check_result()

    # 生成报告
    print('[Check] Generate report')
    TemplateLoader = FileSystemLoader(searchpath=template_path)
    TemplateEnv = Environment(loader=TemplateLoader)
    template = TemplateEnv.get_template(template_file)
    html = template.render(data=check_result)

    # 存储报告
    print('[Check] Save report')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # 发送邮件
    subject = 'System Check Report [%s]' % now_date
    to_list = ['lework@ops.com']

    mail_config = {
        'mail_host': 'smtp.lework.com',
        'mail_port': '465',
        'mail_user': 'ops@lework.com',
        'mail_pass': '123123'
    }
	
    send_mail(mail_config, to_list, subject, html)
