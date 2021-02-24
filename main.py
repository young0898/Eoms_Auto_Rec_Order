import sys
from common.timer import Timer
from spider.spider import Spider

if __name__ == '__main__':
    a = """功能列表：                                                                                
    1、登录OA，保存cookies
    2、跳转方式登录EMOS
    """
    #print(a)

    spider = Spider()
    timer = Timer()

    while(True):
        spider.tousu_order()
        timer.cycleDelay()

