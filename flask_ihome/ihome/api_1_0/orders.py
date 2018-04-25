# -*- coding:utf-8 -*-
"""创建订单,保存订单,查询订单"""""
from datetime import datetime

from flask import current_app
from flask import g
from flask import request, jsonify

from ihome import db
from ihome.api_1_0 import api
from ihome.models import House, Order, User
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET


"""创建订单"""
@api.route(r'/orders', methods=['POST'])
@login_required
def save_order():
    # 1,接收数据hid,sd,ed,
    dict_data = request.json
    hid = dict_data.get('house_id')
    sd = dict_data.get('start_date')
    ed = dict_data.get('end_date')

    # 2,验证有效性
    if not all([hid, sd, ed]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        if sd:
            sd = datetime.strptime(sd, '%Y-%m-%d')
        if ed:
            ed = datetime.strptime(ed, '%Y-%m-%d')
        if sd and ed:
            assert sd <= ed, Exception('结束时间不能小于开始时间')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='日期错误')

    # 2.1获取房源数据user_id,days,price,amount
    try:
        house = House.query.get(hid)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库错误')
    if not house:
        return jsonify(errno=RET.DATAERR, errmsg='该房源不存在')

    user_id = g.user_id
    days = (ed - sd).days
    price = house.price
    amount = price * days

    # 2.2,订单冲突问题
    try:
        conflict_orders = Order.query.filter(Order.house_id == hid, sd < Order.end_date, ed > Order.begin_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询冲突订单失败')
    if conflict_orders:
        return jsonify(errno=RET.DATAEXIST, errmsg='该房源已被预定')

    # 3,创建订单
    order = Order()
    order.house_id = hid
    order.user_id = user_id
    order.begin_date = sd
    order.end_date = ed
    order.days = days
    order.house_price = price
    order.amount = amount

    # 4,保存订单
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='创建订单失败')

    # 5,返回响应
    return jsonify(errno=RET.OK, errmsg='创建订单成功')


"""展示订单"""
@api.route(r'/orders')
@login_required
def show_order():
    # 1,接收数据role,user_id
    role = request.args.get('role')  # 房客,房主
    user_id = g.user_id  # 该用户id

    # 2,验证有效性
    if not all([role, user_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    if role not in ['custom', 'landlord']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='没有该用户')

    # 3,查询订单
    orders_list = []
    if role == 'custom':
        # 查询我定了哪些房子
        orders = user.orders
        for order in orders:
            orders_list.append(order.to_dict())
    elif role == 'landlord':
        # 查询该用户的房源被谁预定了
        houses = user.houses
        houses_id_list = [house.id for house in houses]
        try:
            orders = Order.query.filter(Order.house_id.in_(houses_id_list)).all()
            for order in orders:
                orders_list.append(order.to_dict())
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询数据库错误')

    # 4,返回订单数据
    return jsonify(errno=RET.OK, errmsg='查询到订单数据', data={'orders': orders_list})


"""接单,拒单"""
@api.route(r'/orders/<int:order_id>', methods=['PUT'])
def accept_order(order_id):
    # 1,接收参数,order_id,accept or reject, reason
    action = request.args.get('action')

    # 2,验证数据有效性
    try:
        order = Order.query.get(order_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')
    if action not in ['accept', 'reject']:
        return jsonify(errno=RET.PARAMERR, errmsg='请求方式错误')

    if not order:
        return jsonify(errno=RET.DATAERR, errmsg='没有该订单')

    # 3,修改订单状态,订单数量,拒单原因
    if action == 'accept':
        order.status = 'WAIT_COMMENT'
        try:
            house = House.query.get(order.house_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询数据库错误')
        house.order_count += 1
    else:
        reason = request.json.get('reason')
        order.status = 'REJECTED'
        order.comment = reason

    # 3.1提交数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='修改订单状态失败')

    # 4,返回数据给前端
    return jsonify(errno=RET.OK, errmsg='修改成功')


"""客户添加评价"""
@api.route('/orders/comment', methods=['PUT'])
def add_comment():
    # 1,接收参数,order_id, comment
    dict_data = request.json
    order_id = dict_data.get('order_id')
    comment = dict_data.get('comment', '没有添加评论')

    # 2,验证有效性
    try:
        order = Order.query.get(order_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库错误')
    if not order:
        return jsonify(errno=RET.DATAERR, errmsg='订单不存在')

    # 3,查询订单

    # 4,修改评论,提交数据库
    order.comment = comment
    order.status = 'COMPLETE'
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='评论修改错误')

    # 5,返回成功信息
    return jsonify(errno=RET.OK, errmsg='修改成功')
