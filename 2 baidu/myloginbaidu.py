import requests, time, random, rsa, base64, re
from bs4 import BeautifulSoup as BS
import http.cookiejar as HC
from subprocess import Popen  # 打开图片

home_url = "https://www.baidu.com/"
login_url = "https://passport.baidu.com/v2/api/?login"

headers = {
    "Host": "passport.baidu.com",
    "Referer": "https://www.baidu.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36"
}

# 获取当前时间戳
def get_tt():
    return str(int(time.time() * 1000))


# 随机生成callback
def get_callback():
    prefix = "bd__cbs__"  # callback 前缀
    char = "0123456789abcdefghijklmnopqrstuvwxyz"
    n = random.randint(0, 2147483648)
    suffix = []
    while n != 0:
        suffix.append(char[n % 36])
        n = n // 36
    suffix.reverse()
    print("callback: " + (prefix + ''.join(suffix)))
    return prefix + ''.join(suffix)


# 随机生成gid
def get_gid():
    gid = list("xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    for x in range(len(gid)):
        r = int(random.random() * 16)
        if gid[x] == "x":  # 如果当前值为x
            gid[x] = hex(r).replace("0x", "").upper()
    print("gid: " + "".join(gid))
    return "".join(gid)


def get_token():
    global token_time
    token_time = get_tt()
    call_back = get_callback()
    token_url = "https://passport.baidu.com/v2/api/?getapi&tpl=mn&apiver=v3&tt={}&class=login&gid={}&logintype=dialogLogin&callback={}".format(
        token_time, gid, call_back)
    response = session.get(token_url, headers=headers)
    token_all = response.text.replace(call_back, "")
    token_all = eval(token_all)
    print(token_all)
    return token_all["data"]["token"]


def get_pubkey():
    pubkey_callback = get_callback()
    pubkey_url = "https://passport.baidu.com/v2/getpublickey?token={}&tpl=mn&apiver=v3&tt={}&gid={}&callback={}".format(
        token, get_tt(), gid, pubkey_callback)
    response = session.get(pubkey_url, headers=headers)
    pubkey_all = eval(response.text.replace(pubkey_callback, ""))
    print(pubkey_all["pubkey"], pubkey_all["key"])
    return pubkey_all["pubkey"], pubkey_all["key"]


# 密码rsa加密
def get_rsa_password(psw, pk):
    pub = rsa.PublicKey.load_pkcs1_openssl_pem(pk.encode("utf-8"))
    psw = psw.encode("utf-8")
    passwd = rsa.encrypt(psw, pub)
    passwd = base64.b64encode(passwd)
    print(passwd.decode("utf-8"))
    return passwd.decode("utf-8")

session = requests.session()
session.cookies = HC.LWPCookieJar(filename="BaiDuCookies")
try:
    session.cookies.load(ignore_discard=True)  # 加d载cookies文件
except:
    print("cookie未保存或cookie已过期")
    gid = get_gid()
    session.get("https://passport.baidu.com/v2/?login", headers=headers)
    token = get_token()
    pubkey, key = get_pubkey()
    account = input("请输入您的账号：")
    password = input("请输入您的密码：")

    postData = {
        'staticpage': 'https://www.baidu.com/cache/user/html/v3Jump.html',
        'charset': 'UTF-8',
        'tpl': 'mn',
        'subpro': '',
        'apiver': 'v3',
        'safeflg': '0',
        'u': 'https://www.baidu.com/',
        'isPhone': 'false',
        'detect': '1',
        'quick_user': '0',
        'logintype': 'dialogLogin',
        'logLoginType': 'pc_loginDialog',
        'idc': '',
        'loginmerge': 'true',
        'splogin': 'rate',
        'mem_pass': 'on',
        'crypttype': '12',
        'countrycode': '',
        'codestring': '',
        'verifycode': '',
        'token': token,
        'tt': get_tt(),
        'gid': gid,
        'username': account,
        'password': get_rsa_password(password, pubkey),  # 经过加密
        'rsakey': key,
        'ppui_logintime': str(int(get_tt()) - int(token_time)),
        'callback': get_callback()
    }

    response = session.post(login_url, postData, headers=headers)
    # 如果存在codeString则获取验证码图片，再次请求
    codeString = re.findall(r'codeString=(.*?)&userName', response.text)[0]
    while codeString:
        # 获取图片，保存图片，输入图片验证码
        gif_url = "https://passport.baidu.com/cgi-bin/genimage?{}".format(codeString)
        gif = session.get(gif_url, headers=headers)
        with open("baidu.gif", "wb") as f:
            f.write(gif.content)
        Popen("baidu.gif", shell=True)
        verifycode = input("验证码：")
        postData["verifycode"] = verifycode
        postData["codestring"] = codeString

        # 再次登录
        relogin = session.post(login_url, postData, headers=headers)
        codeString = re.findall(r'codeString=(.*?)&userName', relogin.text)[0]


headers["Host"] = "www.baidu.com"
re = session.get(home_url, headers=headers)
# 保存cookies信息，以备下次直接访问首页
session.cookies.save()
# 获取首页天气信息
print("城市： " + BS(re.text, 'lxml').find("em", {"class": "show-city-name"})["data-key"])
print("气温： " + BS(re.text, 'lxml').find("em", {"class": "show-icon-temp"}).string)
