import sys
from common.timer import Timer
from spider.spider import Spider

if __name__ == '__main__':

    spider = Spider()
    timer = Timer()

    while(True):
        spider.tousu_order()
        timer.cycleDelay()

