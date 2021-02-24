import functools
import requests
import re
from common.request import RequestSession
from common.error import SKException
from common.logger import logger
from common.timer import Timer
from common.config import global_config
from common.javaScript import JavaScipt
from common.helper import (
    response_status
)

class UserLogin:
    """
    用户登录
    """
    def __init__(self, spider_session: RequestSession):
        """
        初始化用户登录
        大致流程：
            1、访问登录页面，获取Token
            2、使用Token获取票据
            3、校验票据
        :param spider_session:
        """
        self.spider_session = spider_session
        self.session = self.spider_session.get_session()
        self.js = JavaScipt()

        self.is_login = False
        self.userName = global_config.get('config', 'userName')
        self.passWord = self.js.get_md5_psswd(global_config.get('config', 'passWord'))
        self.macAddr = global_config.get('config', 'macAddr')
        self.oaHost = global_config.get('config', 'oaHost')
        self.eomsHost = global_config.get('config', 'eomsHost')



        if self.userName:
            self.nick_name = self.userName
        else:
            self.nick_name = 'anonymous'

    def refresh_login_status_OA(self):
        """
        刷新是否登录状态
        :return:
        """
        self.is_login = self._validate_cookies_OA()

    def _validate_cookies_OA(self):
        """
        验证cookies是否有效（是否登陆）
        通过访问用户订单列表页进行判断：若未登录，将会重定向到登陆页面。
        :return: cookies是否有效 True/False
        """
        url = self.oaHost + '/AddressList/newStyle/newStyle20120322/htm/listByDepartForPage.jsp'
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': self.oaHost + '/',
        }
        try:
            resp = self.session.get(url=url, headers=headers, allow_redirects=False)    #params=payload
            #print('cookies验证：',resp.status_code)

            if resp.status_code == requests.codes.OK:
                logger.info("【OA登录】验证cookies有效")
                return True
        except Exception as e:
            logger.error("【OA登录】验证cookies发生异常", e)
        return False

    def _get_login_page_OA(self):
        """
        获取PC端登录页面
        :return:
        """
        url = self.oaHost + "/"
        page = self.session.get(url, headers=self.spider_session.get_headers())
        page.encoding = "UTF-8"
        #print(page.text)
        if response_status(page):
            logger.info('【OA登录】访问OA登录页面成功')
        else:
            logger.error('【OA登录】访问OA登录页面失败')

    def _post_LoginValidate_OA(self):
        """
        验证用户名密码
        :return:
        """
        url = self.oaHost + '/LoginValidate/Servlet/LoginCheck2'
        payload = {
            'userid': self.userName,
            'passwd': self.passWord,
            'macAddr': self.macAddr,
            'isSendSMS': '1',
        }
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': self.oaHost + '/',
        }
        resp = self.session.post(url=url, headers=headers, params=payload)

        if not response_status(resp):
            logger.error('【OA登录】用户名密码验证失败')
            return False

        resp_json = resp.text
        #print('OA用户名密码验证：',resp_json)

        if resp_json == 'true':
            logger.info('【OA登录】用户名密码验证成功')
            return True
        else:
            logger.error('【OA登录】用户名密码验证失败')
            return False

    def _post_Login_OA(self):
        """
        通过用户名密码登录OA
        :return:
        """
        url = self.oaHost + '/wps/myportal'
        payload = {
            'from_login_jsp': 'Y',
            'wps.portlets.userid': self.userName,
            'password': self.passWord,
        }
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': self.oaHost + '/',
        }
        resp = self.session.post(url=url, headers=headers, params=payload)

        if not response_status(resp):
            logger.error('【OA登录】登录失败')
            return False

    def login_by_username_OA(self):
        """
        用户面密码登陆，分三步：
        1、访问OA登录界面（可选）
        2、提交用户名密码进行校验
        3、post提交登录
        :return:
        """
        self.refresh_login_status_OA()  # 刷新用户登录状态
        if self.is_login:
            logger.info('【OA登录】登录成功')
            return

        #OA登录
        #self._get_login_page_OA()     #第一步：访问OA登录界面（可选）
        if self._post_LoginValidate_OA():   #第二步：提交用户名密码进行校验（可省略，此步骤成功后OA会发登录提醒短信）
            self._post_Login_OA()  # 第三步：post提交登录
            self.refresh_login_status_OA()  # 刷新用户登录状态

        if self.is_login:
            logger.info('【OA登录】登录成功')
            self.spider_session.save_cookies_to_local(self.nick_name)  # 保存cookies
        else:
            raise SKException("【OA登录】登录失败")

    def _get_login_page_EOMS(self):
        """
        点击电子运维的链接
        :return:
        """
        url = self.oaHost + "/uniworkSomeLinks/updateSomeLinkClick.do"
        payload = {
            'uid': self.userName,
            'someLinkID': 256,
            'someLinkURL':'0510171C494049040216170D1F410E1D43070B051D0E0B1B0F0D0F095D0C09194213060E001C095B3E372C42191C164B1F010E03070A27041D2D07511706071A170D14091A0713',
        }
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': self.oaHost + '/uniworkSomeLinks/getVaryLink.do?issgs=true',
        }
        resp = self.session.get(url=url, headers=headers, params=payload)
        location_url = resp.headers.get('Location')

        if not response_status(resp):
            logger.error('第一步：点击电子运维链接失败')
            return False
        else:
            logger.info('第一步：点击电子运维链接成功')
            return True

    def _get_login_info_EOMS(self):
        """
        获取电子运维的登录信息
        :return:
        """
        url = self.oaHost + "/websso/SSO.jsp"
        payload = {
            'remoteAppId': 'dianziweihu',
        }
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': self.oaHost + '/uniworkSomeLinks/getVaryLink.do?issgs=true',
        }
        resp = self.session.get(url=url, headers=headers, params=payload)

        if not response_status(resp):
            logger.error('第二步：获取信息失败')
            return False
        else:
            logger.info('第二步：获取信息成功')
            return True

    def _post_Login_EOMS(self):
        """
        通过cookies登录电子运维系统
        :return:
        """
        LtpaToken = requests.utils.dict_from_cookiejar(self.session.cookies).get('LtpaToken')
        url = self.eomsHost + '/eoms35/index.do'
        payload = {
            'method': 'ssoLogin',
            'loginType': 'OA',
        }
        data = {
            'token':LtpaToken,

        }
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': self.oaHost + '/websso/SSO.jsp?remoteAppId=dianziweihu',
        }
        resp = self.session.post(url=url, headers=headers, params=payload, data=data)

        #print(resp)
        #print(resp.headers)
        #print(resp.text)
        # resp_json = resp.text
        # print(resp_json)

        if not response_status(resp):
            logger.error('【EOMS登录】登录失败')
            return False
        else:
            logger.info('【EOMS登录】登录成功')
            return True

    def login_by_cookies_EOMS(self):
        """
        登录EOMS，分三步：
        1、点击电子运维的链接（可选）
        2、提交用户名密码进行校验（可选）
        3、post提交登录
        :return:
        """
        #self._get_login_page_EOMS()     #第一步：点击电子运维的链接（可选）
        #if not self._get_login_info_EOMS():   #第二步：获取登录信息（可选）
        #    return False
        self._post_Login_EOMS()    #第三步：post提交登录

class Spider(object):
    def __init__(self):
        #初始化信息
        self.userName = global_config.get('config', 'userName')
        self.eomsHost = global_config.get('config', 'eomsHost')
        if self.userName:
            self.nick_name = self.userName
        else:
            self.nick_name = 'anonymous'

        #初始化变量
        self.spider_session = RequestSession()
        self.spider_session.load_cookies_from_local(self.nick_name) #如果本地有cookies，则直接加载
        self.Userlogin = UserLogin(self.spider_session)
        self.session = self.spider_session.get_session()
        self.user_agent = self.spider_session.user_agent
        self.timer = Timer()

    def check_login(func):
        """
        用户登录检测，然后发起登录
        """
        @functools.wraps(func)
        def new_func(self, *args, **kwargs):
            logger.info("请登录OA系统")
            self.Userlogin.login_by_username_OA()   #登录OA
            logger.info("------------分隔符------------")
            if self.Userlogin.is_login:
                logger.info("请登录EOMS系统")
                self.Userlogin.login_by_cookies_EOMS()  # 通过cookies登录EOMS
                logger.info("------------分隔符------------")
            return func(self, *args, **kwargs)
        return new_func

    @check_login
    def tousu_order(self):
        """
        投诉接单
        """
        logger.info("获取投诉工单列表")
        page = self.get_tousu_page()
        list = self.get_tousu_list(page)
        self.choose_not_order(list)

    def get_tousu_page(self):

        url = self.eomsHost + '/eoms35/sheet/complaint/complaint.do'
        payload = {
            'method': 'showListsendundo',
            'ssoToken': '170C02021416071A0A55',
        }
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': self.eomsHost + '/eoms35/main.jsp?id=10',
        }
        resp = self.session.get(url=url, headers=headers, params=payload)

        #print(resp)
        # print(resp.headers)
        #print(resp.text)
        return resp.text

    def get_tousu_list(self, resp):
        #f = open("js/编辑5.html", 'r', encoding='UTF-8')
        #resp = f.read()
        #print(resp)
        results = re.findall('<tr class=".*?">\n(.*?)</tr>',resp, re.S)
        #print(results)
        list_arr = []

        for each in results:
            #print(each)
            ones = re.findall('<td.*?>(.*?)</td>\n', each, re.S)
            #print(ones)
            list_one = []
            link = re.findall('window.open[(](.*)[)]; >(.*)</a>', ones[2], re.S)
            start_time = ones[13]
            status = ones[16].replace('\t',"").replace('\n', "").replace('\r', "").replace(' ', "")
            id = link[0][1]

            link_url = link[0][0]
            link_url = self.eomsHost+"/eoms35/sheet/complaint/"+link_url[1:len(link_url)-1]
            #print(id)
            #print(link_url)
            #print(start_time)
            #print(status)
            #print("\n")
            list_one.append(id)
            list_one.append(link_url)
            list_one.append(start_time)
            list_one.append(status)
            #print(list_one)
            list_arr.append(list_one)

        return list_arr

    def choose_not_order(self, list):
        if not list:
            logger.info("投诉工单为空")
            logger.info("+++++++++++++结束符++++++++++++")
            return

        for each in list:
            #处理时间
            #$print(each)
            #判断：未接单和派单时间+30分钟
            if each[3] == "未接单" and self.timer.local_start_time_diff(each[2]):
                logger.info("工单[" + each[0] + "]未接单，派单时间为" + each[2] + "，工单链接为：" + each[1])
            else:
                logger.info("工单[" + each[0] + "]已受理")
        logger.info("+++++++++++++结束符++++++++++++")








