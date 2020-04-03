# インポート
from Crypto.Cipher import AES
import base64

# 定数
CRYPTO_MODE = AES.MODE_CBC

# 特定の長さに調節
def mkpad(s, size):
    s = s.encode('utf-8')
    pad = b' ' * (size - len(s) % size)
    return s + pad

# 暗号化
def encrypt(data, password, iv):
    # 長さの調節
    password = mkpad(password, 16)[:16]
    data = mkpad(data, 16)
    # 暗号化
    try:
        aes = AES.new(password, CRYPTO_MODE, iv)
        data_cipher = aes.encrypt(data)
        return base64.b64encode(data_cipher).decode('utf-8')
    except:
        print('Failed to encrypt.')

# 複合化
def decrypt(encdata, password, iv):
    # 長さの調節
    password = mkpad(password, 16)[:16]
    # 複合か
    try:
        aes = AES.new(password, CRYPTO_MODE, iv)
        encdata = base64.b64decode(encdata)
        data = aes.decrypt(encdata)
        return data.decode('utf-8')
    except:
        print('Failed to decrypt.')
