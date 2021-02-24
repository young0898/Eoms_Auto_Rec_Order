# -*- coding:utf-8 -*-
import time
import requests
import json
import random
from datetime import datetime
from common.logger import logger
from common.config import global_config


class Timer(object):
    def __init__(self):
        self.order_delay_time = int(global_config.get('config', 'order_delay_time'))
        self.cycle_check_time = int(global_config.get('config', 'cycle_check_time'))

    def str_to_time(self, str_time):
        """
        字符串转为时间格式
        :return:
        """
        return int(time.mktime(time.strptime(str_time, '%Y-%m-%d %H:%M:%S')) * 1000)

    def local_time(self):
        """
        获取本地毫秒时间
        :return:
        """
        #localtime = time.localtime(time.time())
        return int(round(time.time() * 1000))

    def local_start_time_diff(self, str_time):
        """
        计算本地与派单时间差
        :return:
        """
        if (self.local_time() - self.str_to_time(str_time)) > self.order_delay_time * 60 * 1000:
            return True
        else:
            return False

    def cycleDelay(self):
        """
        循环查看工单情况的延时
        """
        cycle_time = self.cycle_check_time * 60
        time.sleep(random.randint(cycle_time * 0.8, cycle_time * 1.2))
