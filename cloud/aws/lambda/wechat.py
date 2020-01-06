import json
from botocore.vendored import requests

def lambda_handler(event, context):
    # TODO implement
    url = "https://qyapi.weixin.qq.com"
    
    corpid = ""
    secret = ""
    agentid = ""
    touser = ''
    toparty = ''
    totag = ''

    headers={
        'Content-Type':'application/json'
    }
    
    access_token_url  = '{url}/cgi-bin/gettoken?corpid={id}&corpsecret={crt}'.format(url=url, id=corpid, crt=secret)
    access_token_response = requests.get(url=access_token_url, headers=headers)
    token = json.loads(access_token_response.text)['access_token']

    send_url = '{url}/cgi-bin/message/send?access_token={token}'.format(url=url, token=token)
    message = event['Records'][0]['Sns']
    Timestamp = message['Timestamp']
    Subject = message['Subject']
    sns_message = json.loads(message['Message'])
    region = message['TopicArn'].split(':')[-3]
    state_exclude = ['INSUFFICIENT_DATA']
    
    if sns_message['OldStateValue'] in state_exclude:
        return 
    
    if "ALARM" in Subject:
        title='<font color=\"info\">[aws] 警报！！警报！！</font>'
    elif "OK" in Subject:
        title='<font color=\"info\">[aws] 故障恢复</font>'
    else:
        title='<font color=\"info\">[aws]</font>'
        
    content =  title \
               + "\n> **详情信息**" \
               + "\n> 时间: " + Timestamp \
               + "\n> 内容: " + Subject \
               + "\n> 状态: <font color=\"comment\">{old}</font> => <font color=\"warning\">{new}</font>".format(old=sns_message['OldStateValue'], new=sns_message['NewStateValue'])  \
               + "\n> " \
               + "\n> Region: " + sns_message['Region'] \
               + "\n> Namespace: " + sns_message['Trigger']['Namespace'] \
               + "\n> MetricName: " + sns_message['Trigger']['MetricName'] \
               + "\n> " \
               + "\n> AlarmName: " + sns_message['AlarmName'] \
               + "\n> AlarmDescription: " + sns_message['AlarmDescription'] \
               + "\n> " \
               + "\n> 详情请点击：[Alarm](https://{region}.console.amazonaws.cn/cloudwatch/home?region={region}#s=Alarms&alarm={alarm})".format(region=region, alarm=sns_message['AlarmName'])
    
    msg = {
            "msgtype": 'markdown',
            "agentid": agentid,
            "markdown": {'content': content },
            "safe": 0
        }
        
    if touser:
        msg['touser'] = touser
    if toparty:
        msg['toparty'] = toparty
    if toparty:
        msg['totag'] = totag

    response = requests.post(url=send_url, data=json.dumps(msg), headers=headers)
    
    errcode = json.loads(response.text)['errcode']
    if errcode == 0:
        print('Succesfully')
    else:
        print(response.json())
        print('Failed')
