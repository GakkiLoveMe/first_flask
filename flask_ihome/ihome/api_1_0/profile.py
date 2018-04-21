# -*- coding:utf-8 -*-
"""用于展示个人信息, 图片上传, 用户名修改, 用户实名认证, 显示房源信息"""
from flask import current_app, jsonify
from flask import g
from flask import request
from flask import session

from ihome import db, constants
from ihome.utils.commons import login_required  # 自定义的装饰器
from ihome.api_1_0 import api
from ihome.models import User
from ihome.utils.response_code import RET
from ihome.utils.image_storage import image_storage


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


@api.route(r'/user/avatar', methods=['POST'])
@login_required
def image_upload():
    """用于图片上传"""
    # 1,获取数据id,图片数据
    user_id = g.user_id
    image_data = request.files.get('avatar').read()

    # 2,数据有效性验证
    if not all([user_id, image_data]):
        return jsonify(RET.PARAMERR, errmsg='参数不完整')

    # 3,第三方工具存储图片
    try:
        image_url = image_storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='七牛云上传失败')

    # 4,用户存储图片url
    try:
        user = User.query.filter(User.id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='没有此用户')

    # 保存url
    try:
        user.avatar_url = image_url
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库操作失败')

    # 5,返回上传状态信息
    image_url = constants.QINIU_DOMIN_PREFIX + image_url
    return jsonify(errno=RET.OK, errmsg="上传成功", data={'avatar_url': image_url})


@api.route(r'/user/name', methods=['PUT'])
@login_required
def rename():
    """用于修改用户名"""
    # 1,接收数据,id,new_name
    user_id = g.user_id
    new_name = request.json.get('name')

    # 2,数据校验
    if not all([user_id, new_name]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 3,查询用户
    try:
        user = User.query.filter(User.id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')
    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='没有此用户')
    # 4修改信息,提交数据库
    user.name = new_name
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='更新数据库失败')

    # 5,返回修改状态
    return jsonify(errno=RET.OK, errmsg='用户名修改成功')


@api.route(r'/user/auth')
@login_required
def get_user_auth():
    """获取认证信息"""
    # 1,获取用户id
    user_id = g.user_id

    # 2,查询用户
    try:
        user = User.query.filter(User.id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    # 3,用户有效性判断
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='没有此用户')

    # 4,返回认证信息
    return jsonify(errno=RET.OK, errmsg='认证信息', data=user.user_to_dict())


@api.route(r'/user/auth', methods=['POST'])
@login_required
def set_user_auth():
    """填写用户认证"""
    # 1,接收数据
    user_id = g.user_id

    dict_data = request.json
    real_name = dict_data.get('real_name')
    id_card = dict_data.get('id_card')

    # 2,数据有效性判断
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg='信息不完整')

    # 3,查询用户
    try:
        user = User.query.filter(User.id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    # 4,验证用户是否存在
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='没有此用户')

    # 5,提交用户更改
    user.real_name = real_name
    user.id_card = id_card

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='存储认证信息失败')

    # 6,返回认证状态码
    return jsonify(errno=RET.OK, errmsg='认证信息已修改')


@api.route(r'/users/house')
@login_required
def show_houses():
    """显示发布的房源"""
    # 1,获取用户id
    user_id = g.user_id

    # 查询用户
    try:
        user = User.query.filter(User.id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='产讯数据库失败')

    # 判断是否存在
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='没有此用户')

    # 返回房源信息
    houses = user.houses
    houses_list = []
    for house in houses:
        houses_list.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg='房源信息', data=houses_list)

