#coding=gbk

#coding=utf-8

#-*- coding: UTF-8 -*-  

from ihome.libs.yuntongxun.CCPRestSDK import REST
import ConfigParser

#���ʺ�
accountSid= '8aaf070862b902de0162cc7f389806f5'

#���ʺ�Token
accountToken= '9cbe8c35519841a78d9512a47a0091cd'

#Ӧ��Id
appId='8aaf070862b902de0162cc7f38f606fc'

#�����ַ����ʽ���£�����Ҫдhttp://
serverIP='app.cloopen.com';

#����˿� 
serverPort='8883';

#REST�汾��
softVersion='2013-12-26';

  # ����ģ�����
  # @param to �ֻ�����
  # @param datas �������� ��ʽΪ���� ���磺{'12','34'}���粻���滻���� ''
  # @param $tempId ģ��Id


class CCP(object):
    """�������Ͷ�����"""

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            #��ʼ��REST SDK
            cls._instance.rest = REST(serverIP,serverPort,softVersion)
            cls._instance.rest.setAccount(accountSid,accountToken)
            cls._instance.rest.setAppId(appId)
            return cls._instance
        return cls._instance

    def sendTemplateSMS(self, to, datas, tempId):

        # #��ʼ��REST SDK
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
   
#sendTemplateSMS(�ֻ�����,��������,ģ��Id)
# ccp = CCP()
# ccp.sendTemplateSMS(18222549491, ['999999',5], 1)