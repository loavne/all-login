# -*- coding: utf-8 -*-

""" 知乎登录分为两种登录
    一是手机登录 API : https://www.zhihu.com/login/phone_num
    二是邮箱登录 API : https://www.zhihu.com/login/email

    第一步、打开首页获取_xref值，验证图片
    第二步、输入账号密码
    第三步、看是否需要验证、要则下载验证码图片，手动输入
    第四步、判断是否登录成功、登录成功后获取页面值。

    requests 与 http.cookiejar 相结合使用
    session = requests.session
    session.cookies = http.cookiejar.LWPCookies(filename='abc')
    ...
    请求网址后
    ...
    session.cookies.save()  保存cookies

    加载cookies
    try:
        session.cookies.load(ignore_discard=True)
    except:
        print('没有cookies')
"""

import requests
from bs4 import BeautifulSoup as BS
import time
from subprocess import Popen  # 打开图片
import http.cookiejar
import re

# 模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36'
}
home_url = "https://www.zhihu.com"
base_login = "https://www.zhihu.com/login/"  # 一定不能写成http,否则无法登录

session = requests.session()
session.cookies = http.cookiejar.LWPCookieJar(filename='ZhiHuCookies')
try:
    # 加载Cookies文件
    session.cookies.load(ignore_discard=True)
except:
    print("cookie未保存或cookie已过期")
    # 第一步 获取_xsrf
    _xsrf = BS(session.get(home_url, headers=headers).text, "lxml").find("input", {"name": "_xsrf"})["value"]

    # 第二步 根据账号判断登录方式
    account = input("请输入您的账号：")
    password = input("请输入您的密码：")

    # 第三步 获取验证码图片
    gifUrl = "http://www.zhihu.com/captcha.gif?r=" + str(int(time.time() * 1000)) + "&type=login"
    gif = session.get(gifUrl, headers=headers)
    # 保存图片
    with open('code.gif', 'wb') as f:
        f.write(gif.content)
    # 打开图片
    Popen('code.gif', shell=True)
    # 输入验证码
    captcha = input('captcha: ')

    data = {
        "captcha": captcha,
        "password": password,
        "_xsrf": _xsrf,
    }

    # 第四步 判断account类型是手机号还是邮箱
    if re.match("^.+\@(\[?)[a-zA-Z0-9\-\.]+\.([a-zA-Z]{2,3}|[0-9]{1,3})(\]?)$", account):
        # 邮箱
        data["email"] = account
        base_login = base_login + "email"
    else:
        # 手机号
        data["phone_num"] = account
        base_login = base_login + "phone_num"

    print(data)

    # 第五步 登录
    response = session.post(base_login, data=data, headers=headers)
    print(response.text)

    # 第六步 保存cookie
    session.cookies.save()

# 获取首页信息
resp = session.get(home_url, headers=headers, allow_redirects=False)
print(resp.text)
