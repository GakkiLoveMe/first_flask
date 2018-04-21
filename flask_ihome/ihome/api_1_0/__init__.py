# -*- coding:utf-8 -*-
"""
创建蓝图
"""
from flask import Blueprint

api = Blueprint('api_1_0', __name__)

from . import index
from . import verify, passport, profile, houses
