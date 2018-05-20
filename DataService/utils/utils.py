import rsa
import sys, os, json
import string
"""
 TODO:
    - 所有bytes参数与返回值使用str
    
"""

# rsa方法
def generate_key():
    """
    生成密钥对
    :return: (公钥对象, 私钥对象)
    """
    # 生成密钥
    pubkey, privkey = rsa.newkeys(1024)
    # 保存密钥
    with open('public.pem','w+') as f:
        f.write(pubkey.save_pkcs1().decode())

    with open('private.pem','w+') as f:
        f.write(privkey.save_pkcs1().decode())

    return pubkey, privkey

def load_key():
    """
    加载密钥对
    :return:(公钥对象, 私钥对象)
    """
    try:
        with open('public.pem', 'r') as f:
            pubkey = rsa.PublicKey.load_pkcs1(f.read().encode())

        with open('private.pem', 'r') as f:
            privkey = rsa.PrivateKey.load_pkcs1(f.read().encode())
    except FileNotFoundError:
        pubkey, privkey = generate_key()
    return pubkey, privkey

def pubkey_str():
    """
    获取公钥PEM编码字符串
    :return: 公钥字符串
    """
    pub, priv = load_key()
    return pub.save_pkcs1().decode()

def priv_str():
    """
    获取私钥PEM编码字符串
    :return: 私钥字符串
    """
    pub, priv = load_key()
    return priv.save_pkcs1().decode()

def pub_encrypt(msg):
    """
    公钥加密方法
    :param msg:
    :return: 加密字符串
    """
    pubkey, privkey = load_key()
    crypto = rsa.encrypt(msg.encode(), pubkey)
    return crypto.decode()

def priv_encrypt(msg):
    """
    私钥加密方法
    :param msg:
    :return: 加密字符串
    """
    pubkey, privkey = load_key()
    crypto = rsa.encrypt(msg.encode(), privkey)
    return crypto.decode()

def signature(msg, privkey):
    """
    签名生成
    :param msg: 签名内容
    :param privkey: 私钥字符串
    :return: 签名字符串
    """
    privkey = rsa.PrivateKey.load_pkcs1(privkey)
    return rsa.sign(msg.encode(), privkey, 'SHA-1')

def verify(msg, sign, pubkey, **kwargs):
    """
    签名校验
    :param msg: 签名内容
    :param sign: 签名字符串
    :param pubkey: 公钥字符串
    :return:
    """
    pub = rsa.PublicKey.load_pkcs1(pubkey)

    # print(isinstance(msg, str))
    # msg = bytes(msg, encoding='utf-8')
    # print(isinstance(msg, str))
    if isinstance(msg, str):
        msg = bytes(msg, encoding='utf-8')
    if isinstance(sign, str):
        sign = bytes(sign, encoding='utf-8')
    try:
        # 测试代码
        # print(type(msg))
        # print(type(sign))
        # print(signature(pubkey_str(), kwargs['privkey']))
        # print('############{}'.format(sign))
        rsa.verify(msg, sign, pub)
        return True
    except rsa.pkcs1.VerificationError:
        return False

def pubkey_check(pubkey):
    """
    验证公钥合法性
    :param pubkey:
    :return:
    """
    try:
        rsa.PublicKey.load_pkcs1(pubkey)
    except Exception as e:
        print(repr(e))
        return False
    return True

def get_conf_from_json(path=None):
    """
    获取json配置文件
    :param path: 配置文件路径
    :return: Dict
    """
    if path is None:
        path = 'conf.json'
    f = sys._getframe()
    filename = f.f_back.f_code.co_filename
    file_dir = os.path.split(os.path.abspath(filename))[0]  # 实现相对目录导入
    if path[0] is not '/':  # 处理同目录文件的情况
        path = '/' + path
    path = file_dir + path
    # print(path)
    try:
        with open(path, 'r') as f:
            config = json.load(f)
    except IOError as e:
        print(e)
        return None
    # print(config)
    return config

def formating_check(str):
    """
    格式校验
    :param str:
    :return:
    """
    alphas = string.ascii_letters + '_'
    nums = string.digits
    alphanums = alphas + nums
    if str[0] not in alphas:
        return False
    else:
        for i in str[1:]:
            if i not in alphanums:
                return False
    return True

def str2bool(str):
    if type(str) == bool:
        return str
    if str == 'True':
        return True
    if str == 'False':
        return False
    return None

if __name__ == '__main__':
    generate_key()