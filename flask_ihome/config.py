# -*- coding:utf-8 -*-
"""
应用程序配置文件
"""
import redis
import logging


class BaseConfig:
    """启动配置类"""
    # 设置签名
    SECRET_KEY = 'SDJFKSDJFK'

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@localhost:3306/flask_ihome'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # session配置
    SESSION_TYPE = "redis"  # 指定session的保存位置
    SESSION_USE_SIGNER = True  # 设置session存储签名
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # SESSION_PERMANENT = 1111
    PERMANENT_SESSION_LIFETIME = 24*3600 * 2  # session的有效时间,单位秒


class Developer(BaseConfig):
    """开发者环境"""

    DEBUG = True

    DEBUG_LEVEL = logging.DEBUG


class Production(BaseConfig):
    """生产环境"""

    DEBUG_LEVEL = logging.ERROR


config_dict = {
    'develop': Developer,
    'product': Production
}
