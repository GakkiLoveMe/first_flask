# -*- coding:utf-8 -*-
"""
创建蓝图,用于优化静态文件的访问
"""
from flask import Blueprint
from flask import current_app, request
from flask_wtf.csrf import generate_csrf  # 用于生成csrftoken

html = Blueprint('web_html', __name__)


@html.route(r'/<re(".*"):file_name>')  # 自定义参数转换器re
def get_html_page(file_name):
    # print current_app.static_folder

    # index判断
    if not file_name:
        file_name = 'index.html'

    # 拼接路径
    if file_name != 'favicon.ico':
        file_name = 'html/' + file_name

    # 根据文件名查找并读取文件
    response = current_app.send_static_file(file_name)
    # print request.cookies.get('session')

    # 生成csrftoken, 并设置
    csrf = generate_csrf()
    response.set_cookie('csrf_token', csrf)

    return response
