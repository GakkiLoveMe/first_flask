# -*- coding:utf-8 -*-
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from config import config_dict
# from flask_session import Session
#
#
# app = Flask(__name__)
#
# # 添加配置信息
# app.config.from_object(config_dict['develop'])
#
# # 创建数据库对象
# db = SQLAlchemy(app)
#
# # 初始化session
# Session(app)
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from ihome import create_app
from ihome import db


# 通过ihome项目文件,获取应用
app = create_app(pattern='develop')

# @app.route(r'/')
# def index():
#     return 'hello world'
# 创建应用管理对象
manager = Manager(app)

# 关联app与db
Migrate(app, db)

# 添加迁移命令
manager.add_command('db', MigrateCommand)


if __name__ == "__main__":
    print app.url_map
    manager.run()
