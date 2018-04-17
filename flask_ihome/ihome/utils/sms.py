#coding=gbk

#coding=utf-8

#-*- coding: UTF-8 -*-  

from ihome.libs.yuntongxun.CCPRestSDK import REST
import ConfigParser

#主帐号
accountSid= '8aaf070862b902de0162cc7f389806f5'

#主帐号Token
accountToken= '9cbe8c35519841a78d9512a47a0091cd'

#应用Id
appId='8aaf070862b902de0162cc7f38f606fc'

#请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com';

#请求端口 
serverPort='8883';

#REST版本号
softVersion='2013-12-26';

  # 发送模板短信
  # @param to 手机号码
  # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
  # @param $tempId 模板Id


class CCP(object):
    """创建发送对象单例"""

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            #初始化REST SDK
            cls._instance.rest = REST(serverIP,serverPort,softVersion)
            cls._instance.rest.setAccount(accountSid,accountToken)
            cls._instance.rest.setAppId(appId)
            return cls._instance
        return cls._instance

    def sendTemplateSMS(self, to, datas, tempId):

        # #初始化REST SDK
        # rest = REST(serverIP,serverPort,softVersion)
        # rest.setAccount(accountSid,accountToken)
        # rest.setAppId(appId)

        result = self.rest.sendTemplateSMS(to,datas,tempId)
        # for k,v in result.iteritems():
        #
        #     if k=='templateSMS' :
        #             for k,s in v.iteritems():
        #                 print '%s:%s' % (k, s)
        #     else:
        #         print '%s:%s' % (k, v)
        #
        if result['statusCode'] == '000000':
            return 0
        else:
            return -1
   
#sendTemplateSMS(手机号码,内容数据,模板Id)
# ccp = CCP()
# ccp.sendTemplateSMS(18222549491, ['999999',5], 1)