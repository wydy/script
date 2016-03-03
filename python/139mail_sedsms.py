# coding:utf-8
import requests
import urllib


# 利用139邮箱发短信功能发送免费短信，以达到即使报警信息。
# 短信收费说明：
# 计费周期赠 30 条，超出按 0.1元/条 计费。
# 向联通、电信用户发短信，与本地资费相同，不计入赠送条数。
# 一次可发给10个号码，每天限发250条，每月限发2500条。
# by lework
# 2015年4月12日

def send_sms(cmcc_tel, cmcc_passwd, send_phone, content):
    """
    :param cmcc_tel:    139邮箱账号
    :param cmcc_passwd: 账号密码
    :param send_phone:  发送的手机号
    :param content: 	发送的内容
    :return: 			返回('Sent:', '15821******', 'Success')
    """

    if not cmcc_tel.strip() or not cmcc_passwd.strip() or not send_phone.strip() or not content.strip():
        return 'Error: Parameter error'
    if len(content) >= 70:
        return 'Error: Exceeded the character limit'

    # 登录139邮箱
    url = "https://wapmail.10086.cn/index.htm"
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q:0.9,image/webp,*/*;q:0.8',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Host': 'wapmail.10086.cn',
        'Referer': 'http://wapmail.10086.cn/',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0'
    }
    data = {
        'ur': cmcc_tel,
        'pw': cmcc_passwd
    }
    cmcc_session = requests.Session()
    try:
        cmcc_res = cmcc_session.post(url, headers=headers, data=data)
        user_sid = cmcc_res.url.split('&')
        user_vn = user_sid[2].replace('vn=', '')
        user_sid = user_sid[0].split('=')[1]
    except:
        return 'Error: Login Connection Failed'

    if cmcc_res.url == url:
        return 'Error: login Failed'

    # 发送短信
    sms_url = "http://m.mail.10086.cn/ws12/w3/w3smsend"

    sms_hearder = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q:0.9,image/webp,*/*;q:0.8',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Host': 'm.mail.10086.cn',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Referer': 'http://m.mail.10086.cn/bv12/sendsms.html?&sid=%s&vn=%s&vid=&cmd=40' % (user_sid, user_vn),
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0'
    }
    sms_data = {
        'sid': user_sid,
        'vn': user_vn,
        'cmd': '2',
        'content': content,
        'reciever': send_phone
    }
    try:
        sms_send = cmcc_session.post(sms_url, headers=sms_hearder, data=sms_data)
    except:
        return 'Error: Send Connection Failed'

    sms_result = urllib.unquote(sms_send.text)
    sms_result = eval(sms_result.replace('null', '"null"').encode('utf-8'))

    # 登出139邮箱
    logout_url = "http://m.mail.10086.cn/wp12/w3/logout"
    logout_data = {
        'sid': user_sid,
        'vn': user_vn
    }

    logout_hearder = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q:0.9,image/webp,*/*;q:0.8',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Host': 'm.mail.10086.cn',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Referer': 'http://m.mail.10086.cn/bv12/home.html?&sid=%s&vn=%s' % (user_sid, user_vn),
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0'
    }

    logout_send = cmcc_session.post(logout_url, headers=logout_hearder, data=logout_data)
    # 返回代码
    if str(sms_result['result']['eroerCode']) == '0':
        return 'Sent:', send_phone, 'Success'
    else:
        return 'Sent:', send_phone, 'Failed'


if __name__ == "__main__":
    send = send_sms('1871*****', '*********', '158215*****', u'报警信息：警告')
    print send
