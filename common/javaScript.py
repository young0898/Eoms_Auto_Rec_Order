import execjs
# 执行本地的md5.js
class JavaScipt():
    def __init__(self):
        self.sType = 32

    def get_js(self):
        f = open("js/md5.js", 'r', encoding='UTF-8')
        line = f.readline()
        htmlstr = ''
        while line:
            htmlstr = htmlstr + line
            line = f.readline()
        return htmlstr

    def get_md5_psswd(self, passwd, sType=32):
        js_str = self.get_js()
        ctx = execjs.compile(js_str) #加载JS文件
        md5_passwd = ctx.call('MD5',passwd, sType)  #调用js方法  第一个参数是JS的方法名，后面的data和key是js方法的参数
        return md5_passwd


if __name__ == '__main__':
    js = JavaScipt()
    print(js.get_md5_psswd("Zy@202011",32))