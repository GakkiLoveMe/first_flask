# -*- coding:utf-8 -*-
"""
用于自定义路径转换器, 自定义装饰器
"""
from werkzeug.routing import BaseConverter
from flask import session, g, jsonify
from functools import wraps
from ihome.utils.response_code import RET


class RegexConverter(BaseConverter):

    def __init__(self, url_map, regex):

        super(RegexConverter, self).__init__(url_map)
        self.regex = regex


# 用户登陆验证
def login_required(view_func):
    @wraps(view_func)  # 用于防止修改原函数的__name__属性
    def inner(*args, **kwargs):
        g.user_id = session.get('user_id')

        if g.user_id:
            return view_func(*args, **kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    return inner
