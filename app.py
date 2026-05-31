# ====================== app.py FULL VỚI DEBUG CHI TIẾT ======================

from flask import Flask, request, jsonify
import json
import base64
import requests
import urllib3
import time
import logging
import sys
import os
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

urllib3.disable_warnings()

# ====================== LOGGING CHI TIẾT ======================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/ban_api_debug.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ====================== CONSTANTS ======================
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
    except Exception as e:
        logger.error(f"decode_ff_name error: {e}")
        return "Unknown"

def decode_jwt(token):
    try:
        payload_part = token.split('.')[1]
        payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload_part)
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception as e:
        logger.error(f"decode_jwt error: {e}")
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
    except Exception as e:
        logger.error(f"get_available_room error: {e}")
        return {}

def build_majorlogin(tok, open_id, p_type):
    return enc(SimpleProtobuf.create_login_payload(open_id, tok, str(p_type)))

# ====================== HÀM CHÍNH CÓ DEBUG ======================
def fetch_majorlogin_jwt(token):
    token = token.strip()
    logger.info("="*60)
    logger.info(f"START fetch_majorlogin_jwt")
    logger.info(f"Token input: {token[:50]}...")
    logger.info(f"Token length: {len(token)}")
    logger.info(f"Token starts with 'eyJ': {token.startswith('eyJ')}")
    logger.info(f"Token dot count: {token.count('.')}")
    logger.info("="*60)
    
    # ========== TRƯỜNG HỢP 1: ĐÃ LÀ JWT ==========
    if token.startswith("eyJ") and token.count('.') == 2 and len(token) > 200:
        logger.info("[CASE 1] Input is JWT, using directly")
        try:
            decoded = decode_jwt(token)
            logger.info(f"JWT decoded: account_id={decoded.get('account_id')}, nickname={decoded.get('nickname')}")
            if decoded.get('account_id'):
                logger.info("[CASE 1] SUCCESS - Returning JWT")
                return token, decoded, None
            else:
                logger.warning("[CASE 1] JWT decoded but no account_id")
        except Exception as e:
            logger.error(f"[CASE 1] JWT decode error: {e}")
    
    # ========== TRƯỜNG HỢP 2: ACCESS TOKEN ==========
    logger.info("[CASE 2] Treating as Access Token")
    
    # Bước 2.1: Gọi API inspect Garena
    open_id = None
    account_id = None
    
    logger.info("[STEP 2.1] Calling Garena OAuth inspect API...")
    try:
        inspect_url = f"https://100067.connect.garena.com/oauth/token/inspect?token={token}"
        logger.info(f"URL: {inspect_url}")
        resp = requests.get(inspect_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        logger.info(f"Status code: {resp.status_code}")
        logger.info(f"Response raw: {resp.text[:500]}")
        
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"Response JSON: {json.dumps(data, default=str)[:500]}")
            open_id = data.get('open_id')
            account_id = data.get('account_id') or data.get('uid')
            logger.info(f"Extracted - open_id: {open_id}, account_id: {account_id}")
        else:
            logger.error(f"Inspect API failed with status {resp.status_code}")
    except Exception as e:
        logger.error(f"Inspect API error: {e}")
    
    # Bước 2.2: Gọi jwt-caidb để convert
    logger.info("[STEP 2.2] Calling jwt-caidb convert API...")
    jwt_token = None
    decoded = None
    
    try:
        convert_url = f"https://jwt-caidb.vercel.app/convert/{token}"
        logger.info(f"URL: {convert_url}")
        resp = requests.get(convert_url, timeout=10)
        logger.info(f"Status code: {resp.status_code}")
        logger.info(f"Response raw: {resp.text[:500]}")
        
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"Response JSON: {json.dumps(data, default=str)[:500]}")
            
            if data.get('success'):
                jwt_token = data.get('jwt_token')
                decoded = data.get('decoded', {})
                logger.info(f"Convert success! JWT length: {len(jwt_token) if jwt_token else 0}")
                logger.info(f"Decoded: account_id={decoded.get('account_id') if decoded else 'N/A'}")
                
                if jwt_token and len(jwt_token) > 200:
                    logger.info("[STEP 2.2] SUCCESS - Returning converted JWT")
                    return jwt_token, decoded, None
            else:
                logger.warning(f"Convert API returned success=False: {data.get('error', 'unknown')}")
        else:
            logger.error(f"Convert API failed with status {resp.status_code}")
    except Exception as e:
        logger.error(f"Convert API error: {e}")
    
    # Nếu có open_id từ inspect, thử MajorLogin trực tiếp
    if open_id:
        logger.info("[STEP 2.3] Trying MajorLogin with open_id...")
        platforms = [8, 3, 4, 6]
        
        for p_type in platforms:
            logger.info(f"Trying platform: {p_type}")
            try:
                pl = build_majorlogin(token, open_id, p_type)
                logger.info(f"Payload built, size: {len(pl)} bytes")
                
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
                        logger.error(f"Decrypt failed: {e}")
                        hex_data = x.content.hex()
                        logger.info(f"Raw hex length: {len(hex_data)}")
                    
                    parsed = get_available_room(hex_data)
                    logger.info(f"Parsed fields: {list(parsed.keys())}")
                    
                    # Tìm JWT trong response
                    for key, value in parsed.items():
                        data_val = value.get('data', '')
                        if isinstance(data_val, str) and len(data_val) > 50:
                            logger.info(f"Field {key}: value preview = {data_val[:100]}...")
                            if data_val.startswith("eyJ") or ('.' in data_val and len(data_val.split('.')) == 3):
                                logger.info(f"[STEP 2.3] SUCCESS - Found JWT in field {key}")
                                return data_val, decode_jwt(data_val), None
                    
                    logger.warning(f"No JWT found for platform {p_type}")
                else:
                    logger.warning(f"MajorLogin failed with status {x.status_code}")
            except Exception as e:
                logger.error(f"MajorLogin platform {p_type} error: {e}")
    
    logger.error("[FAILED] All methods failed")
    return None, None, "Cannot extract JWT from token"

def trigger_ban(jwt_token, version):
    logger.info(f"[BAN] Triggering ban with JWT: {jwt_token[:50]}...")
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
    logger.info(f"[BAN] Request headers: {json.dumps(headers, default=str)[:200]}")
    logger.info(f"[BAN] Body size: {len(body)} bytes")
    
    resp = requests.post(API_URL, headers=headers, data=body, timeout=20, verify=False)
    logger.info(f"[BAN] Response status: {resp.status_code}")
    logger.info(f"[BAN] Response size: {len(resp.content)} bytes")
    
    return resp

# ====================== API ENDPOINTS ======================
@app.route('/ban', methods=['GET', 'POST'])
def ban_account():
    logger.info("="*60)
    logger.info("[ENDPOINT] /ban called")
    
    if request.method == 'GET':
        token = request.args.get('token') or request.args.get('access_token')
    else:
        data = request.get_json() or {}
        token = data.get('token') or data.get('access_token')
    
    logger.info(f"Token received: {token[:50] if token else 'None'}...")
    
    if not token:
        logger.error("[ENDPOINT] No token provided")
        return jsonify({
            'success': False,
            'error': 'Missing token parameter',
            'usage': 'GET /ban?token=<your_token> or POST {"token": "xxx"}'
        }), 400
    
    try:
        # Bước 1: Lấy JWT
        logger.info("[ENDPOINT] Calling fetch_majorlogin_jwt...")
        jwt_token, decoded, error = fetch_majorlogin_jwt(token)
        
        if not jwt_token:
            logger.error(f"[ENDPOINT] Authentication failed: {error}")
            return jsonify({
                'success': False,
                'error': error or 'Failed to authenticate token',
                'token_provided': token[:30] + '...' if len(token) > 30 else token
            }), 401
        
        logger.info(f"[ENDPOINT] JWT obtained, length: {len(jwt_token)}")
        
        # Giải mã thông tin
        raw_nick = decoded.get('nickname', '')
        nickname = decode_ff_name(raw_nick)
        account_id = decoded.get('account_id', 'Unknown')
        region = decoded.get('lock_region', decoded.get('region', 'Unknown'))
        version = decoded.get('release_version', 'OB53')
        
        logger.info(f"[ENDPOINT] Target: {nickname} | {account_id} | {region} | {version}")
        
        # Bước 2: Gửi payload ban
        logger.info("[ENDPOINT] Calling trigger_ban...")
        ban_response = trigger_ban(jwt_token, version)
        
        if ban_response.status_code == 200:
            logger.info("[ENDPOINT] Ban successful!")
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
            logger.error(f"[ENDPOINT] Ban failed with status {ban_response.status_code}")
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
        logger.error(f"[ENDPOINT] Exception: {str(e)}")
        logger.error(f"[ENDPOINT] Exception type: {type(e)}")
        import traceback
        logger.error(f"[ENDPOINT] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/debug', methods=['GET'])
def debug_info():
    token = request.args.get('token', '')
    logger.info(f"[DEBUG] Checking token: {token[:50] if token else 'None'}...")
    
    result = {
        'token_input': token[:50] + '...' if len(token) > 50 else token,
        'token_length': len(token),
        'token_starts_eyJ': token.startswith('eyJ'),
        'token_dot_count': token.count('.'),
        'is_jwt': token.startswith('eyJ') and token.count('.') == 2 and len(token) > 200
    }
    
    # Test JWT decode
    if result['is_jwt']:
        try:
            decoded = decode_jwt(token)
            result['jwt_decode_success'] = True
            result['jwt_payload'] = decoded
            exp = decoded.get('exp', 0)
            result['expired'] = exp < time.time() if exp else 'unknown'
            result['expired_time'] = datetime.fromtimestamp(exp).isoformat() if exp else 'N/A'
        except Exception as e:
            result['jwt_decode_success'] = False
            result['jwt_decode_error'] = str(e)
    
    # Test inspect API
    try:
        inspect_url = f"https://100067.connect.garena.com/oauth/token/inspect?token={token}"
        resp = requests.get(inspect_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        result['inspect_api_status'] = resp.status_code
        if resp.status_code == 200:
            result['inspect_api_response'] = resp.json()
    except Exception as e:
        result['inspect_api_error'] = str(e)
    
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


@app.route('/log', methods=['GET'])
def view_log():
    try:
        log_file = '/tmp/ban_api_debug.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.read().split('\n')
                # Lấy 200 dòng cuối
                logs = '\n'.join(lines[-200:])
            return jsonify({
                'success': True,
                'log_lines': len(lines),
                'logs': logs
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


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'Free Fire Ban API',
        'version': '2.0',
        'endpoints': {
            '/ban': 'GET or POST with token parameter',
            '/debug': 'GET with token parameter to debug',
            '/log': 'GET to view debug logs'
        },
        'example': '/ban?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3636, debug=True)
