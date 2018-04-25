# -*- coding:utf-8 -*-
"""
显示区域, 发布新房源, 显示房源信息, 上传图片, 显示热门房源, 搜索房源信息
"""""
from datetime import datetime
from flask import current_app, jsonify
from flask import g
from flask import json
from flask import request

from ihome import constants
from ihome import redis_store, db
from ihome.api_1_0 import api
from ihome.models import Area, User, Facility, House, HouseImage, Order
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.utils.image_storage import image_storage


"""显示地区"""
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


"""发布新房源"""
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


"""上传房屋图片"""
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


"""主页显示热门房源"""
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


"""搜索房源"""
@api.route(r'/houses')
def search_houses():
    # 0.1,接收数据
    aid = request.args.get('aid')  # 区域
    sd = request.args.get('sd', '')  # 开始时间
    ed = request.args.get('ed', '')  # 结束时间
    sk = request.args.get('sk', 'new')  # 排序规则
    p = request.args.get('p')  # 第几页数据
    house_query = House.query  # 设置查询变量

    # 页码数据转换,参数校验
    try:
        p = int(p)
        if sd:  # TODO 数据格式转换
            sd = datetime.strptime(sd, '%Y-%m-%d')
        if ed:
            ed = datetime.strptime(ed, '%Y-%m-%d')
        if sd and ed:
            assert sd <= ed, Exception('开始时间不能大于结束时间')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='分页数据格式不正确')

    # 查询redis缓存数据
    try:
        redis_key = 'search_%s_%s_%s_%s' % (aid, sd, ed, sk)
        resp = redis_store.hget(redis_key, p)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询缓存失败')

    if resp:
        return jsonify(errno=RET.OK, errmsg='缓存数据', data=eval(resp))  # eval,返回输入数据的默认格式

    # 1,查询数据库
        # 0.2,判断是否有区域信息
    try:
        if aid:
            house_query = house_query.filter(House.area_id == aid)

        # 0.3,入住时间和退房时间判断
        conflict_order = []  # 冲突订单
        if sd and ed:
            # 有开始时间和结束事件
            try:
                conflict_order = Order.query.filter(sd < Order.end_date, ed > Order.begin_date).all()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg='订单查询失败')

        elif sd:
            # 只有开始时间
            try:
                conflict_order = Order.query.filter(sd < Order.end_date).all()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg='订单查询失败')

        elif ed:
            # 只有结束时间
            try:
                conflict_order = Order.query.filter(ed > Order.begin_date).all()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg='订单查询失败')

        # 判断是否有数据
        if conflict_order:
            conflict_list = [order.house_id for order in conflict_order]
            house_query = house_query.filter(House.id.notin_(conflict_list))

        # 0.4,进行排序,订单多少,价格
        if sk == 'booking':
            house_query = house_query.order_by(House.order_count.desc())
        elif sk == 'price-inc':
            house_query = house_query.order_by(House.price)
        elif sk == 'price-des':
            house_query = house_query.order_by(House.price.desc())

        # 0.5,数据分页
        paginator = house_query.paginate(p, 2)
        houses = paginator.items
        total_pages = paginator.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    # 2,判断数据有效性
    if not houses:
        return jsonify(errno=RET.DATAERR, errmsg='没有房源信息')

    # 3,返回数据
    houses_list = [house.to_basic_dict() for house in houses]
    resp_data = {'houses': houses_list, 'total_page': total_pages}

    # 4,redis缓存数据
    try:
        pipeline = redis_store.pipeline()  # 创建管道对象, 用来事务操作
        # 开启事务
        pipeline.multi()

        # 储存数据, 设置过期时间
        redis_key = 'search_%s_%s_%s_%s' % (aid, sd, ed, sk)
        redis_store.hset(redis_key, p, resp_data)
        redis_store.expire(redis_key, constants.HOUSE_LIST_REDIS_EXPIRES)
        # 执行事务
        pipeline.execute()
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg='房源信息', data=resp_data)


"""房屋详尽信息"""
@api.route(r'/houses/<int:house_id>')
@login_required
def house_detail(house_id):
    # 接收数据,user_id
    user_id = g.user_id

    # 查询数据库
    try:
        house = House.query.filter(House.id == house_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    # 判断数据有效行
    if not house:
        return jsonify(errno=RET.DATAERR, errmsg='没有数据')

    # 返回响应
    resp = {'house': house.to_full_dict(), 'user_id': user_id}
    return jsonify(errno=RET.OK, errmsg='返回数据', data=resp)
