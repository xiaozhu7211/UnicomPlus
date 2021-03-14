import requests,json,time,re,login,logging,traceback,os,random,notify,datetime
from lxml.html import fromstring
import pytz


#用户登录全局变量
client = None


#读取用户配置信息
#错误原因有两种：格式错误、未读取到错误
def readJson():
    try:
        #用户配置信息
        with open('./config.json','r') as fp:
            users = json.load(fp)
            return users
    except Exception as e:
        print(traceback.format_exc())
        logging.error('账号信息获取失败错误，原因为: ' + str(e))
        logging.error('1.请检查是否在Secrets添加了账号信息，以及添加的位置是否正确。')
        logging.error('2.填写之前，是否在网站验证过Json格式的正确性。')


#获取积分余额
#分类：奖励积分、定向积分、通信积分
def getIntegral():
    try:
        integral = client.post('https://m.client.10010.com/welfare-mall-front/mobile/show/bj2205/v2/Y')
        integral.encoding = 'utf-8'
        res = integral.json()
        for r in res['resdata']['data']:
            #排除掉优惠卷日志
            if r['name'] != '优惠券':
                logging.info('【'+r['name']+'】: ' + r['number'])
        time.sleep(1)
    except Exception as e:
        print(traceback.format_exc())
        logging.error('【积分余额】: 错误，原因为: ' + str(e))






#获得我的礼包页面对象
def getQuerywinning(username):
    #获得我的礼包页面
    querywinninglist = client.get(
        'http://m.client.10010.com/myPrizeForActivity/querywinninglist.htm?yw_code=&desmobile='+str(username)+'&version=android@8.0100')
    querywinninglist.encoding = 'utf-8'
    #将页面格式化
    doc = f"""{querywinninglist.text}"""
    #转换为html对象
    html = fromstring(doc)
    return html

#存储并返回未使用的流量包
def getStorageFlow(username):
    #获得我的礼包页面
    html = getQuerywinning(username)
    #寻找ul下的所有li，在未使用流量包栏页面
    ul = html.xpath('/html/body/div[1]/div[7]/ul/li')
    #存储流量包数据
    datas = []
    #获得所有流量包的标识并存储
    for li in ul:
        data = {
            'activeCode': None,
            'prizeRecordID': None,
            'phone': None
        }
        tran = {1:'activeCode',2:'prizeRecordID',3:'phone'}
        line = li.attrib.get('onclick')
        #正则匹配字符串 toDetailPage('2534','20210307073111185674422127348889','18566669999');
        pattern = re.finditer(r'\'[\dA-Za-z]+\'',line)
        i = 1
        for match in pattern:
            data[tran[i]] = match.group()[1:-1]
            i = i + 1
        datas.append(data)
    return datas

#获取Asia/Shanghai时区时间戳
def getTimezone():
    timezone = pytz.timezone('Asia/Shanghai')
    dt = datetime.datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
    timeArray = time.strptime(dt, "%Y-%m-%d %H:%M:%S")
    timeStamp = int(time.mktime(timeArray))
    return timeStamp

#获得流量包的还剩多长时间结束，返回形式时间戳
def getflowEndTime(username):
    #获得中国时间戳
    now = getTimezone()
    #获得我的礼包页面对象
    html = getQuerywinning(username)
    #获得流量包到期的时间戳
    endStamp = []
    endTime = html.xpath('/html/body/div[1]/div[7]/ul/li[*]/div[2]/p[3]')
    for end in endTime:
        #寻找起止时间间隔位置
        #end为空，可能无到期时间和开始时间
        end = end.text
        if end != None:
            index = end.find('-')+1
            #切割得到流量包失效时间
            end = end[index:index+10] + ' 23:59:59'
            end = end.replace('.','-')
            #将时间转换为时间数组
            timeArray = time.strptime(end, "%Y-%m-%d %H:%M:%S")
            #得到时间戳
            timeStamp = int(time.mktime(timeArray))
            endStamp.append(timeStamp-now)
        else:
            #将找不到结束时间的流量包设置为不激活
            endStamp.append(86401)
    return endStamp

#激活即将过期的流量包
def actionFlow(username):
    #获得所有未使用的流量包
    datas = getStorageFlow(username)
    #获得流量包还剩多长时间到期时间戳
    endTime = getflowEndTime(username)
    #流量包下标
    i = 0
    flag = True
    for end in endTime:
        #如果时间小于1天就激活
        #程序早上7：30运行，正好当天可使用
        if end < 86400:
            flag = False
            param = 'activeCode='+datas[i]['activeCode']+'&prizeRecordID='+datas[i]['prizeRecordID']+'&activeName='+'做任务领奖品'
            activeData = {
                'activeCode': datas[i]['activeCode'],
                'prizeRecordID': datas[i]['prizeRecordID'],
                'activeName': '做任务领奖品'
            }
            #激活流量包
            res = client.post('http://m.client.10010.com/myPrizeForActivity/myPrize/activationFlowPackages.htm',data=activeData)
            res.encoding = 'utf-8'
            res = res.json()
            if res['status'] == '200':
                logging.info('【即将过期流量包】: ' + '激活成功')
            else:
                logging.info('【即将过期流量包】: ' + '激活失败')
            time.sleep(8)
        i = i + 1
    if flag:
        logging.info('【即将过期流量包】: 暂无')



#主函数入口
if __name__ == '__main__':
    main("","")
