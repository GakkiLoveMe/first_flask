# -*- coding:utf-8 -*-
"""
配置蓝图函数
"""
from . import api
from ihome import models
import logging


@api.route(r'/', methods=['GET', 'POST'])
def index():
    # session['']
    logging.debug("调试信息")
    logging.info("详情信息")
    logging.warning("警告信息")
    logging.error("错误信息")

    return 'hahah'