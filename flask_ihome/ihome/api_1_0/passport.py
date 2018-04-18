# -*- coding:utf-8 -*-
"""注册和登陆逻辑"""
import re

from flask import current_app, session
from flask import request, jsonify

from ihome import redis_store, db
from ihome.api_1_0 import api
from ihome.models import User
from ihome.utils.response_code import RET


@api.route(r'/user', methods=['POST'])
def user_register():
    """注册
    """
    # 1,获取手机号，短信验证码，密码
    dict_data = request.json

    mobile = dict_data.get('mobile')
    phoneCode = dict_data.get('phoneCode')
    pwd = dict_data.get('password')

    # 2,验证数据有效性
    if not all([mobile, phoneCode, pwd]):
        return jsonify(errno=RET.PARAMERR, errmsg='填写信息不完整')

    if not re.match(r'1[35678]\d{9}', mobile):
        return jsonify(errno=RET.DATAERR, errmsg='手机号错误')
    # TODO 密码验证

    # 3,短信验证码确认,是否过期,是否正确
    # 读取短信码
    try:
        sms_code = redis_store.get('sms_code:' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库操作错误')

    if not sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg='短信码已失效')
    if sms_code != phoneCode:
        return jsonify(errno=RET.DATAERR, errmsg='短信码输入错误')

    # 4,创建user对象并保存
    user = User()
    user.name = mobile
    user.mobile = mobile
    user.password = pwd  # TODO 密码加密

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='创建用户失败')

    # 5,记录用户状态
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_mobile'] = user.mobile

    # 6,返回注册状态给前端
    return jsonify(errno=RET.OK, errmsg='注册成功')


@api.route(r'/session', methods=['POST'])
def user_login():
    """用户登陆逻辑"""
    # 1,获取数据,用户名和密码
    dict_data = request.json

    user_name = dict_data.get('mobile')
    pwd = dict_data.get('password')

    # 2,验证数据有效性
    if not all([user_name, pwd]):
        return jsonify(errno=RET.PARAMERR, errmsg='用户名和密码不能为空')

    # 验证密码错误次数
    try:
        num = redis_store.get('pwd_error_num:' + user_name)
    except Exception as e:
        current_app.logger.error(e)
        num = 0

    try:
        num = int(num)
    except Exception as e:
        current_app.logger.error(e)
        num = 0

    if num >= 5:
        return jsonify(errno=RET.PWDERR, errmsg='请十分钟后再试')

    # 4,判断用户是否存在
    try:
        user = User.query.filter(User.name==user_name).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库操作错误')

    if not user:
        return jsonify(errno=RET.USERERR, errmsg='没有此用户')

    # 3,判断密码是否正确
    if not user.check_password(pwd):
        # 存储错误次数
        redis_store.incr('pwd_error_num:' + user_name)  # 每次该key的值自动加一
        redis_store.expire('pwd_error_num:' + user_name, 10)  # 过期时间
        return jsonify(errno=RET.PWDERR, errmsg='密码错误')

    # 5,记录登陆状态
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_mobile'] = user.mobile

    # 6,返回登陆成功的状态信息
    return jsonify(errno=RET.OK, errmsg='登陆成功')
