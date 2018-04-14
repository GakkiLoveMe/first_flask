# -*- coding:utf-8 -*-
"""
通过项目创建初始化app并返回
"""
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from config import config_dict
from flask_session import Session
from flask_wtf.csrf import CSRFProtect


# 创建数据库对象
db = SQLAlchemy()

# 创建csrf对象
csrf = CSRFProtect()


def create_app(pattern='product'):
    """用于创建app"""

    # 创建日志记录文件
    log_file()

    # 创建app
    app = Flask(__name__)

    # 添加配置信息
    app.config.from_object(config_dict.get(pattern))

    # 数据库绑定app
    db.init_app(app)

    # 初始化session
    Session(app)

    # 注册蓝图
    from api_1_0 import api  # 解决循环倒包问题
    app.register_blueprint(api)

    # 添加csrftoken验证
    csrf.init_app(app)

    return app


def log_file():
    """用于处理log日志"""

    # 设置日志的记录等级
    logging.basicConfig(level=logging.DEBUG)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=100, backupCount=10)
    # 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日记录器
    logging.getLogger().addHandler(file_log_handler)