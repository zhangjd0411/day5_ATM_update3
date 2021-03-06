#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:xieshengsen

import os
import sys
from core import auth
from core import logger
from core import accounts
from core import transaction
from core import db_handler
from conf import settings
import datetime
import time


trans_logger = logger.logger('transaction')
access_logger = logger.logger('access')

user_data = {
    'account_id': None,
    'is_authenticated': False,
    'account_data': None
}


def display_account_info(account_data):
    ignore_display = ["password"]
    for k in account_data:
        if k in ignore_display:
            continue
        else:
            print("{:<20}:\033[32;1m{:<20}\033[0m".format(k, account_data[k]))


def display_account_info_manage(account_data):
    ignore_display = ["password"]
    for k in account_data:
        if k in ignore_display:
            continue
        else:
            print("{:<20}:\033[32;1m{:<20}\033[0m".format(k, account_data[k]))


def account_info(acc_data):
    """
    打印登录用户帐户信息
    :param acc_data: 登录信息
    :return:
    """
    account_id = acc_data["account_id"]
    account_data = acc_data["account_data"]
    status = account_data["status"]
    if status == 8:  # 管理员
        new_account_id = input("\033[32;1m请输入查找用户的ID:\033[0m>>>:").strip()
        new_account_data = auth.acc_check(new_account_id)  # 管理员获取普通用户信息
        new_status = new_account_data["status"]
        if new_status == 8 and account_id != new_account_id:
            return True
    display_account_info(account_data)
    return True


def account_info_manage(acc_data):
    account_id = acc_data["account_id"]
    account_data = acc_data["account_data"]
    status = account_data["status"]
    if status == 8:  # 管理员
        new_account_id = input("\033[32;1m请输入查找用户的ID:\033[0m>>>:").strip()
        new_account_data = auth.acc_check(new_account_id)  # 管理员获取普通用户信息
        new_status = new_account_data["status"]
        if new_status == 8 and account_id != new_account_id:
            return True
        display_account_info_manage(new_account_data)
    return True


def pay(amount):
    acc_data = get_user_data()
    account_data = accounts.load_current_balance(acc_data['account_id'])
    if amount > 0:
        new_balance = transaction.make_transaction(trans_logger, account_data, 'pay', amount)
        if new_balance:
            return True
    else:
        print('[\033[31;1m%s\033[0m] is not a valid amount, only accept integer!' % amount)
        return None


def repay(acc_data):
    """
    账单还款函数
    :param acc_data:
    :return:
    """
    account_data = accounts.load_current_balance(acc_data['account_id'])
    current_balance = """-*-*-*-*-*-*-*-*- 账户余额信息 -*-*-*-*-*-*-*-*-
        Credit :    %s
        Balance:    %s\n"""% (account_data['credit'], account_data['balance'])
    print(current_balance)
    back_flag = False
    while not back_flag:
        repay_amount = input("\033[32;1m 请输入还款余额\033[0m[q=quit]>>>:").strip()
        if repay_amount.isdigit():
            repay_amount = int(repay_amount)

            old_balance = account_data['balance']
            old_credit = account_data["credit"]
            if old_credit >= 30000:
                print ("信用卡余额充足，不需要还款~")
                continue
            if old_balance <= repay_amount:
                print ("还款金额不足，请充值后再来~")
            old_balance = account_data['balance']
            new_credit = old_credit + repay_amount
            new_balance = old_balance - repay_amount
            account_data["credit"] = new_credit
            account_data['balance'] = new_balance
            accounts.dump_account(account_data)
            print ("还款成功，重新登录后生效~")
            return True
        elif repay_amount == 'q':
            back_flag = True
        else:
            print("[\033[31;1m 输入不合法，请重新输入\033[0m]")
            continue


def withdraw(acc_data):
    '''
    账单取款函数
    :param acc_data:
    :return:
    '''
    account_data = accounts.load_current_balance(acc_data['account_id'])
    current_balance = ''' -*-*-*-*-*-*-*-*- 账户余额信息 -*-*-*-*-*-*-*-*-
        Credit :    %s
        Balance:    %s\n''' % (account_data['credit'], account_data['balance'])
    print(current_balance)
    back_flag = False
    while not back_flag:
        withdraw_amount = input("请输入取款余额[q=quit]>>>:").strip()
        if len(withdraw_amount) > 0 and withdraw_amount.isdigit():
            new_balance = transaction.make_transaction(trans_logger, account_data, 'withdraw', withdraw_amount)
            time.sleep(0.1)
            if new_balance:
                print('''\033[42;1m余额总数:%s\033[0m,重新登录后生效~''' % (new_balance['balance']))
        elif withdraw_amount == 'q':
            back_flag = True
        else:
            print("[\033[31;1m输入不合法，请重新输入\033[0m]")


def transfer(acc_data):
    '''
    打印当前余额，并转帐
    :param acc_data:
    :return:
    '''
    account_data = accounts.load_current_balance(acc_data['account_id'])
    current_balance = ''' -*-*-*-*-*-*-*-*- 账户信息 -*-*-*-*-*-*-*-*-
        Credit :    %s
        Balance:    %s
        ''' % (account_data['credit'], account_data['balance'])
    print(current_balance)
    back_flag = False
    while not back_flag:
        receiver = input("\033[33;1m收款人:\033[0m[q=quit]>>>:").strip()  # 收款人
        if receiver == account_data["id"]:
            print("\033[31;1m收款人不能为自己\033[0m")
            continue
        elif receiver == "q":
            break
        else:
            receiver_account_data = auth.acc_check(receiver)
            status = receiver_account_data['status']
            if status == 0:
                transfer_amount = input("\033[33;1m收款金额:\033[0m[q=quit]").strip()
                if len(transfer_amount) > 0 and transfer_amount.isdigit():
                    new_balance = transaction.make_transaction(trans_logger, account_data, 'transfer', transfer_amount)
                    transaction.make_transaction(trans_logger, receiver_account_data, 'receive', transfer_amount)
                    if new_balance:
                        print('''\033[42;1m帐号余额:%s\033[0m''' % (new_balance['balance']))

                else:
                    print('[\033[31;1m输入不合法，请重新输入\033[0m]')

                if transfer_amount == 'q':
                    back_flag = True
        if transfer == 'q':
            back_flag = True


def pay_check(acc_data):
    """
    查询帐单详情
    :param acc_data:
    :return:
    """
    bill_date = input("Please input the date you will query "
                      "like [\033[32;1m2016-12\033[0m]>>>").strip()
    log_path = db_handler.db_handler(settings.LOG_DATABASE)
    bill_log = "%s/%s.bills" % (log_path, acc_data['account_id'])
    if not os.path.exists(bill_log):
        print("Account [\033[32;1m%s\033[0m] is no bills." % acc_data["account_id"])
        return

    print("Account [\033[32;1m%s\033[0m] bills:" % acc_data["account_id"])
    print("-".center(50, "-"))
    with open(bill_log, "r") as f:
        for bill in f:
            print(bill)
            b_date = bill.split(" ")[0]  # 帐单月份
            if bill_date == b_date:
                print("\033[33;1m%s\033[0m" % bill.strip())

    log_type = "transaction"
    print("Account [\033[32;1m%s\033[0m] history log:" % acc_data["account_id"])
    logger.show_log(acc_data['account_id'], log_type, bill_date)


def save(acc_data):
    """
    存钱
    :param acc_data:
    :return:
    """
    account_data = accounts.load_current_balance(acc_data['account_id'])
    current_balance = ''' --------- 信用卡信息 --------
        Credit :    %s
        Balance:    %s

    ''' % (account_data['credit'], account_data['balance'])
    print(current_balance)
    back_flag = False
    while not back_flag:
        save_amount = input("请输入存款金额[b=back]>>>:").strip()
        if save_amount == 'b':
            back_flag = True
        elif len(save_amount) > 0 and save_amount.isdigit():
            save_amount = int(save_amount)
            old_balance = account_data['balance']
            new_balance = old_balance + save_amount
            # new_balance = transaction.make_transaction(trans_logger, account_data, 'save', save_amount)
            account_data['balance'] = new_balance
            accounts.dump_account(account_data)
            time.sleep(0.1)
            print("充值成功，账号余额为\033[32;1m%s\033[0m，重新登录后生效" % new_balance)
            return True
            # if new_balance:
            #     # account_data['balance'] = new_balance
            #     # accounts.dump_account(account_data)
            #     # print('''\033[42;1mNew Balance:%s\033[0m''' % (new_balance['balance']))
            #     back_flag = True
        else:
            print('输入错误~')


def logout(acc_data):
    time.sleep(2)
    exit("-*-*-*-*-*-*-*-*- 再见 -*-*-*-*-*-*-*-*-")


def interactive(acc_data):
    status = acc_data["account_data"]["status"]
    if status == 8:
        print ("\033[31;1m%s\033[0m用户为管理员"% acc_data["account_id"])

    menu = u'''
    -*-*-*-*-*-*- ATM信用卡中心 -*-*-*-*-*-*-\033[32;1m
    0.  退出信用卡中心
    1.  信用卡账户信息
    2.  信用卡还款
    3.  信用卡取款
    4.  信用卡转账
    5.  信用卡存款
    \033[0m'''
    menu_dict = {
        '1': account_info,
        '2': repay,
        '3': withdraw,
        '4': transfer,
        '5': save,
        '0': logout,
    }
    exit_flag = False
    while not exit_flag:
        print(menu)
        user_option = input("请选择操作[0=exit]>>>:").strip()
        if user_option in menu_dict:
            menu_dict[user_option](acc_data)
        else:
            print("\033[31;1m输入的操作不合法\033[0m")


def get_bill(account_id):
    '''
    生成帐单，定于每月25日
    :param account_id: 帐户id
    :return:
    '''
    i = datetime.datetime.now()
    year_month = "%s-%s" % (i.year, i.month)
    account_data = accounts.load_current_balance(account_id)
    balance = account_data["balance"]
    credit = account_data["credit"]

    if balance >= credit:
        repay_amount = 0
        bill_info = "%s用户不需要还款"% account_id
    else:
        repay_amount = credit - balance
        bill_info = "%s还款的利息%s"% (account_id, repay_amount)
    print (bill_info)
    log_path = db_handler.db_handler(settings.LOG_DATABASE)
    bill_log = "%s/%s.bills" % (log_path, account_id)
    print (bill_log)
    # with open(bill_log, "a+") as f:
    #     f.write("bill_date: %s account_id: %s need_repay: %d\n" % (year_month, account_id, repay_amount))


def get_all_bill():
    '''
    生成全部可用用户的帐单
    :return:
    '''
    db_path = db_handler.db_handler(settings.DATABASE)
    for root, dirs, files in os.walk(db_path):
        for file in files:
            if os.path.splitext(file)[1] == '.json':
                account_id = os.path.splitext(file)[0]
                account_data = auth.acc_check(account_id)
                # status = account_data['status']
            print("\033[33;1m帐单已经生成,请查看transactions.log\033[0m~~")

                # if status == 8:
                #     display_account_info(account_data)
                #     get_bill(account_id)
                # else:
                #     pass
    return True


def check_admin(func):
    """
    检查是否管理员
    :param func:
    :return:
    """
    def inner(*args, **kwargs):
        if user_data['account_data'].get('status', None) == 8:
            ret = func(*args, **kwargs)
            return ret
        else:
            print('\033[31;1mPermission denied\033[0m')
    return inner


@check_admin
def manage_func(acc_data):
    """
    管理员的功能
    :return:
    """
    menu = u'''
    -*-*-*-*-*-*- 管理员平台 -*-*-*-*-*-*-\033[32;1m
    0.  退出管理平台
    1.  创建用户信息
    2.  查询用户信息
    3.  修改用户信息
    4.  生成用户帐单
    \033[0m'''
    menu_dic = {
        '0': 'logout(acc_data)',
        '1': 'auth.sign_up()',
        '2': 'account_info_manage(acc_data)',
        '3': 'auth.modify()',
        '4': 'get_all_bill()'}

    go_flag = True
    while go_flag:
        print(menu)
        user_option = input("请输入操作[0=exit]>>>:").strip()
        if user_option in menu_dic.keys():
            go_flag = eval(menu_dic[user_option])
        else:
            print("\033[41;1m操作失败，请重新输入\033[0m")


def get_user_data():
    account_data = auth.acc_login(user_data, access_logger)
    if user_data['is_authenticated']:
        user_data['account_data'] = account_data
        return user_data
    else:
        return None


def run():
    print("\n-*-*-*-*-*-*-*--*-*- ATM信用卡中心 -*-*-*-*-*-*-*-*-*-*-*-\n")
    user_data = get_user_data()
    interactive(user_data)


def manage_run():
    print("\n-*-*-*-*-*-*-*-*-*-*- 管理员平台 -*-*-*-*-*-*-*-*-*-*-\n")
    user_data = get_user_data()
    manage_func(user_data)