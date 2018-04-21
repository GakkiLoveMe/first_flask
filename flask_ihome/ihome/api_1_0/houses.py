# -*- coding:utf-8 -*-
"""显示区域, 发布新房源, 显示房源信息, 上传图片, 显示热门房源"""
from flask import current_app, jsonify
from flask import g
from flask import json
from flask import request

from ihome import constants
from ihome import redis_store, db
from ihome.api_1_0 import api
from ihome.models import Area, User, Facility, House, HouseImage
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.utils.image_storage import image_storage


@api.route(r'/areas')
def get_areas():
    """显示地区"""
    # 优化数据读取,优从缓存中读取
    try:
        areas = redis_store.get('areas')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='地区缓存读取错误')

    if areas:
        # 转换数据格式
        areas = json.loads(areas)
        return jsonify(errno=RET.OK, errmsg="地区信息", data=areas)

    # 1,读取数据库
    try:
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库错误")

    # 2,转为字典
    areas_list = []
    for area in areas:
        areas_list.append(area.to_dict())

    # 3.存储到redis中
    try:
        redis_store.set('areas', json.dumps(areas_list))
    except Exception as e:
        current_app.logger.error(e)

    # 3,返回数据
    return jsonify(errno=RET.OK, errmsg="地区信息", data=areas_list)


@api.route(r'/houses', methods=['POST'])
@login_required
def houses():
    """发布新房源"""
    # 1,获取用户id
    user_id = g.user_id

    # 2,查询用户
    try:
        user = User.query.filter(User.id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户失败')

    # 3,验证是否存在
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='该用户不存在')

    # 4,接收房源数据
    dict_data = request.json
    title = dict_data.get('title')
    price = dict_data.get('price')
    area_id = dict_data.get('area_id')
    address = dict_data.get('address')
    room_count = dict_data.get('room_count')
    acreage = dict_data.get('acreage')
    unit = dict_data.get('unit')
    capacity = dict_data.get('capacity')
    beds = dict_data.get('beds')
    deposit = dict_data.get('deposit')
    min_days = dict_data.get('min_days')
    max_days = dict_data.get('max_days')

    # 修改数据格式,price和deposit
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据转化错误')

    # 5,接收房源设施数据
    facilitys = dict_data.get('facility')  # 设施列表,id

    # 查询设施名称
    try:
        facilitys = Facility.query.filter(Facility.id.in_(facilitys)).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    # facility_names = []
    # for facility in facilitys:
    #     facility_names.append(facility.name)

    # 6,创建新房源
    house = House()
    house.title = title
    house.price = price
    house.area_id = area_id
    house.address = address
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days
    house.facilities = facilitys
    house.user_id = user_id
    # 7,保存新房源
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库存储失败')

    # 8,返会房源id,用于存储图片
    return jsonify(errno=RET.OK, errmsg='创建房源成功', data={'house_id': house.id})


@api.route(r'/houses/<int:house_id>/images', methods=['POST'])
def house_image_upload(house_id):
    """上传房屋图片"""
    # 1获取房屋id, 上传图片
    image_data = request.files.get('house_image').read()

    # 2查询房屋对象
    try:
        house = House.query.filter(House.id == house_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    # 3验证是否存在
    if not house:
        return jsonify(errno=RET.DATAERR, errmsg='房屋信息不存在')

    # 4七牛云上传图片
    try:
        image_url = image_storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='七牛云上传失败')

    # 5数据库保存图片地址, 创建房屋图片对象
    house_image = HouseImage()
    house_image.house_id = house.id
    house_image.url = image_url

    house.index_image_url = image_url

    try:
        db.session.add(house_image)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='存储图片失败')

    # 返回图片地址
    return jsonify(errno=RET.OK, errmsg='上传成功', data={"url": constants.QINIU_DOMIN_PREFIX + image_url})


@api.route(r'/houses/index')
def index_houses():
    """显示热门房源"""
    # 1,查询所有房源,并排序
    try:
        houses = House.query.order_by(House.order_count.desc()).limit(5)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    # 2,返回房源图片
    house_image_list = []
    for house in houses:
        house_image_list.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg='返回图片', data={'houses': house_image_list})

