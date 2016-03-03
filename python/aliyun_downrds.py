# coding:utf-8


import requests
import urllib
import base64
import hmac
import time
import json
import uuid
import logging
from hashlib import sha1
import os 

# 阿里云rds数据库自动备份下载

logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='H:\\download.log',
                filemode='a')

#################################################################################################
#定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


def sign(accessKeySecret, parameters):
    #===========================================================================
    # '''签名方法
    # @param secret: 签名需要的密钥
    # @param parameters: 支持字典和string两种
    # '''
    #===========================================================================
    # 如果parameters 是字典类的话

    sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])

    canonicalizedQueryString = ''
    for (k,v) in sortedParameters:
        canonicalizedQueryString += '&' + percent_encode(k) + '=' + percent_encode(v)
    stringToSign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])

    h = hmac.new(accessKeySecret + "&", stringToSign, sha1)
    signature = base64.encodestring(h.digest()).strip()
    return signature

def percent_encode(encodeStr):
    encodeStr = str(encodeStr)
    res = urllib.quote(encodeStr, '')
    res = res.replace('+', '%20')
    res = res.replace('*', '%2A')
    res = res.replace('%7E', '~')
    return res

def CreateBackup(apikey,apisecret):
	cdb_parameters = { \
	    'Format'        : 'json', \
	    'Version'   : '2014-08-15', \
	    'AccessKeyId'   : apikey, \
	    'SignatureVersion'  : '1.0', \
	    'SignatureMethod'   : 'HMAC-SHA1', \
	    'SignatureNonce'    : str(uuid.uuid1()), \
	    'TimeStamp'         : timestamp, \
		'Action'        : 'CreateBackup', \
	    'DBInstanceId'      : 'rdswb45274s******',\
		'BackupMethod'		: 'Physical',\
		'BackupType'		: 'FullBackup'
	}

	signature = sign(apisecret,cdb_parameters)
	cdb_parameters['Signature'] = signature
	url = "/?" + urllib.urlencode(cdb_parameters)
	try:
		apireq = requests.get(apiurl+url)
	except:
		logging.error(u'网络连接失败')
		exit()
	return apireq.json()

def getdownurl(apikey,apisecret): 
	parameters = { \
	    'Format'        : 'json', \
	    'Version'   : '2014-08-15', \
	    'AccessKeyId'   : apikey, \
	    'SignatureVersion'  : '1.0', \
	    'SignatureMethod'   : 'HMAC-SHA1', \
	    'SignatureNonce'    : str(uuid.uuid1()), \
	    'TimeStamp'         : timestamp, \
		'Action'        : 'DescribeBackups', \
	    'DBInstanceId'      : 'rdswb452********',\
		'StartTime'			: starttime,\
		'EndTime'			: endtime
	}
	signature = sign(apisecret,parameters)
	parameters['Signature'] = signature
	url = "/?" + urllib.urlencode(parameters)
	try:
		apireq = requests.get(apiurl+url)
	except:
		logging.error(u'网络连接失败')
		exit()
	try:
		url  = apireq.json()['Items']['Backup'][0]['BackupDownloadURL']
		print apireq.json()['Items']['Backup']
	except:
		logging.error(u'没有获取到下载地址')
		exit()
	return url
	
def downurl(url,PWD):
	Name = url.split('?')[0]
	Name = Name.split('/')[4]
	if os.path.isfile(PWD+Name):
		logging.error(u'文件已存在: %s' % Name)
	else:
		try:
			r = requests.get(url,stream=True)
			with open(PWD+Name, 'wb') as fd:
				for chunk in r.iter_content():
					fd.write(chunk)
		except:
			logging.ERROR(u'下载文件失败')
			exit()
		logging.info(u'数据库下载完成：%s'  % str(url))


if __name__ == "__main__":
	apiurl = 'http://rds.aliyuncs.com'
	apikey = 'vSs*********'
	apisecret = ''
	timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
	starttime = time.strftime("%Y-%m-%dT00:00Z", time.gmtime())

	result = CreateBackup(apikey,apisecret)
	logging.info(u'创建备份任务 %s' % str(result))
	logging.info(u'等待300秒钟') 
	time.sleep(300)
	
	endtime = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())
	dburl = getdownurl(apikey,apisecret)
	logging.info(u'获取备份数据库下载地址： %s' % str(dburl))

	logging.info(u'开始下载')
	downurl(dburl,u"H:\\db\\")