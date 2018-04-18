# -*- coding:utf-8 -*-
"""用于展示个人信息"""
from flask import current_app, jsonify
from flask import session

from ihome.api_1_0 import api
from ihome.models import User
from ihome.utils.response_code import RET


@api.route(r'/user')
def user_profile():
    """显示个人信息"""
    # 1,获取手机号
    mobile = session.get('user_mobile')

    if not mobile:
        return jsonify(errno=RET.SESSIONERR, errmsg='登录信息已过期')

    # 2,查询用户
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库操作错误')

    # 3,验证用户是否存在
    if not user:
        return jsonify(errno=RET.USERERR, errmsg='该用户不存在')

    # 4,读取用户名和头像信息

    # 5, 发送给前端
    return jsonify(errno=RET.OK, errmsg='发送成功', data=user.user_to_dict())
