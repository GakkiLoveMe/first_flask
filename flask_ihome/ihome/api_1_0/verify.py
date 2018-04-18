# -*- coding:utf-8 -*-
"""
用于图片验证和短信验证
"""
from flask import current_app
from flask import json
from flask import make_response
from flask import request, jsonify
from ihome.api_1_0 import api
from ihome.models import User
from ihome.utils.captcha.captcha import captcha
from ihome import constants
from ihome import redis_store  # redis存储对象
from flask import logging
import re, random
from ihome.utils.sms import CCP
from ihome.utils.response_code import RET


@api.route(r'/image_code')
def get_image_code():
    """图片验证"""
    # 接收请求数据
    cur_id = request.args.get('cur_id')
    pre_id = request.args.get('pre_id')

    # 通过第三方包获取图片
    name, text, image_data = captcha.generate_captcha()

    # 数据库中保存信息, 删除已有信息
    try:
        redis_store.delete('image_code:' + pre_id)
        redis_store.set('image_code:' + cur_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库操作异常')

    # 修改返回数据格式
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/jpg'

    # 返回数据
    return response


@api.route(r'/sms_code', methods=['POST'])
def get_sms_code():
    """用于短信验证"""
    # 1,获取请求信息,图片验证码,手机号,图片id
    json_data = request.data
    json_dict = json.loads(json_data)

    image_code = json_dict.get('image_code')
    image_id = json_dict.get('image_code_id')
    mobile = json_dict.get('mobile')

    # 2,判断数据有效性
    if not all([image_code, image_id, mobile]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    if not re.match(r'1[345678]\d{9}', mobile):
        return jsonify(errno=RET.DATAERR, errmsg='手机号错误')

    # 判断用户是否注册
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库操作错误')
    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg='该用户已存在')

    # 3,图片验证 码判断
    try:
        redis_image_code = redis_store.get('image_code:' + image_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库操作错误')

    if not redis_image_code:
        return jsonify(errno=RET.DATAERR, errmsg='验证码已失效')

    if redis_image_code != image_code:
        return jsonify(errno=RET.DATAERR, errmsg='验证码输入错误')

    # 删除图片验证码
    try:
        redis_store.delete('image_code:' + image_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='图片验证码删除异常')

    # 4,发送短信
    # 生成短信码
    sms_code = '%06d' % random.randint(0, 999999)

    try:
        ccp = CCP()
        result = ccp.sendTemplateSMS(mobile, [sms_code, 5], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='短信发送失败')

    # 短信发送状态码验证
    if result == '-1':
        return jsonify(errno=RET.THIRDERR, errmsg='短信发送失败')

    # 5,redis中储存短信验证
    try:
        redis_store.set('sms_code:' + mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='短信信息存储失败')

    # 6,获取状态返回给前端
    return jsonify(errno=RET.OK, errmsg='短信发送成功')
