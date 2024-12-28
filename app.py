# from flask import Flask, request, jsonify, send_from_directory
# import os
# from flask_cors import CORS
# from Crypto.Random import get_random_bytes
# import base64
# import cbor2
# import redis
# import json
# from typing import Dict

# app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes

# # Redis cache class
# class RedisCache:
#     def __init__(self):
#         self.r = redis.Redis(
#             host='localhost',
#             port=6379,
#             decode_responses=True,
#             username="default",
#             # password="lwP4oIeR6bnrzKioTYCfwNOvw9FSBW31"
#         )

#     def get(self, key: str) -> Dict:
#         try:
#             data = self.r.get(key)
#             return json.loads(data) if data else None
#         except redis.RedisError:
#             return None
            
#     def set(self, key: str, value: Dict, expiry: int = 3600):
#         try:
#             self.r.set(key, json.dumps(value), ex=expiry)
#         except redis.RedisError:
#             pass

# # Initialize Redis cache
# cache = RedisCache()

# @app.route('/')
# def serve_index():
#     return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

# # Utility function to generate a random challenge
# def generate_challenge():
#     return base64.urlsafe_b64encode(get_random_bytes(32)).rstrip(b'=').decode('utf-8')

# # Endpoint: Start the registration process
# @app.route('/register/start', methods=['POST'])
# def register_start():
#     data = request.json
#     username = data.get('username')
#     if not username:
#         return jsonify({'error': 'Username is required'}), 400

#     # Check if the device has already registered a credential
#     existing_credentials = cache.get('credentials')
#     print("Existing Credentials:", existing_credentials)
#     if existing_credentials:
#         for cred in existing_credentials.values():
#             if cred.get('username') != username:
#                 return jsonify({'error': 'This device has already registered with a different username'}), 400

#     challenge = generate_challenge()
#     cache.set(username, {'challenge': challenge})  # Store challenge in Redis

#     publicKeyCredentialCreationOptions = {
#         'challenge': challenge,
#         'rp': {
#             'name': 'Demo Site',
#             'id': 'localhost',
#         },
#         'user': {
#             'id': base64.urlsafe_b64encode(get_random_bytes(16)).rstrip(b'=').decode('utf-8'),
#             'name': username,
#             'displayName': username,
#         },
#         'pubKeyCredParams': [
#             {'type': 'public-key', 'alg': -7},  # ES256
#             {'type': 'public-key', 'alg': -257}  # RS256
#         ],
#         'authenticatorSelection': {
#             'userVerification': 'discouraged',
#         },
#         'timeout': 60000,
#         'attestation': 'direct',
#     }

#     return jsonify(publicKeyCredentialCreationOptions)

# # Endpoint: Complete the registration process
# @app.route('/register/complete', methods=['POST'])
# def register_complete():
#     data = request.json
#     username = data.get('username')
#     credential = data.get('credential')
#     user = cache.get(username)

#     if not user:
#         return jsonify({'error': 'User not found'}), 400

#     # Basic check that the credential object exists
#     if not credential or not credential.get('id') or not credential.get('response'):
#         return jsonify({'error': 'Invalid credential'}), 400

#     # Minimal verification placeholder
#     # For production, parse and validate 'credential.response.clientDataJSON' and 'attestationObject'
#     # using a trusted library like 'fido2-lib'.
#     if not credential['response'].get('attestationObject'):
#         return jsonify({'error': 'Missing attestation object'}), 400

#     credential_id = credential['id']
#     if cache.get(credential_id):
#         return jsonify({'error': 'Credential already registered with a different username'}), 400

#     # Parse the attestationObject to extract the public key
#     attestation_object = base64.urlsafe_b64decode(credential['response']['attestationObject'] + '==')
#     attestation_data = cbor2.loads(attestation_object)
#     auth_data = attestation_data['authData']
#     public_key_cbor = auth_data[-77:]  # Extract the last 77 bytes which contain the public key
#     public_key = cbor2.loads(public_key_cbor)
#     print("Public Key:", public_key)

#     # Store credential in Redis (for demo purposes)
#     user.update({
#         'credentialId': credential_id,
#         'publicKey': credential['response']['attestationObject'],
#     })
#     cache.set(username, user)
#     cache.set(credential_id, username)

#     return jsonify({'success': True})

# if __name__ == '__main__':
#     app.run(host='localhost', port=3000)

from flask import Flask, request, jsonify, send_from_directory
import os
from flask_cors import CORS
from Crypto.Random import get_random_bytes
import base64
import cbor2
import redis
import json
from typing import Dict, List, Optional
from datetime import datetime  # Import datetime module

app = Flask(__name__)
CORS(app)

class RedisCache:
    def __init__(self):
        self.r = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True,
            username="default"
        )

    def get(self, key: str) -> Dict:
        try:
            data = self.r.get(key)
            return json.loads(data) if data else None
        except redis.RedisError:
            return None
            
    def set(self, key: str, value: Dict, expiry: int = 3600):
        try:
            self.r.set(key, json.dumps(value), ex=expiry)
        except redis.RedisError:
            pass
    
    def get_all_credentials(self) -> Dict[str, Dict]:
        """Get all credential mappings from Redis"""
        try:
            # Get all keys that start with 'credential:*'
            keys = self.r.keys('credential:*')
            credentials = {}
            for key in keys:
                data = self.get(key)
                if data:
                    credentials[key.replace('credential:', '')] = data
            return credentials
        except redis.RedisError:
            return {}

cache = RedisCache()

@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

def generate_challenge():
    return base64.urlsafe_b64encode(get_random_bytes(32)).rstrip(b'=').decode('utf-8')

def get_credential_by_username(username: str) -> Optional[Dict]:
    """Get credential information for a given username"""
    credentials = cache.get_all_credentials()
    for cred_id, cred_data in credentials.items():
        if cred_data.get('username') == username:
            return {'id': cred_id, **cred_data}
    return None

@app.route('/register/start', methods=['POST'])
def register_start():
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    # Check if username is already registered
    existing_user_credential = get_credential_by_username(username)
    if existing_user_credential:
        return jsonify({'error': 'Username already registered'}), 400

    # Get all existing credentials to check for device reuse
    existing_credentials = cache.get_all_credentials()
    
    # Extract attestation info from request (this would come from the authenticator)
    # In a real implementation, you'd get this from the device fingerprint or authenticator data
    user_agent = request.headers.get('User-Agent', '')
    device_fingerprint = user_agent  # Simplified for demo - you should use a more robust method

    # Check if this device has registered before with a different username
    for cred_data in existing_credentials.values():
        if cred_data.get('device_fingerprint') == device_fingerprint:
            return jsonify({
                'error': 'This device has already been registered with a different username'
            }), 400

    challenge = generate_challenge()
    
    # Store registration attempt data
    cache.set(f'registration:{username}', {
        'challenge': challenge,
        'device_fingerprint': device_fingerprint
    })

    publicKeyCredentialCreationOptions = {
        'challenge': challenge,
        'rp': {
            'name': 'Demo Site',
            'id': 'localhost',
        },
        'user': {
            'id': base64.urlsafe_b64encode(get_random_bytes(16)).rstrip(b'=').decode('utf-8'),
            'name': username,
            'displayName': username,
        },
        'pubKeyCredParams': [
            {'type': 'public-key', 'alg': -7},  # ES256
            {'type': 'public-key', 'alg': -257}  # RS256
        ],
        'authenticatorSelection': {
            'userVerification': 'discouraged',
            'authenticatorAttachment': 'platform',  # Enforce platform authenticator
            'requireResidentKey': True,  # Require resident key
        },
        'timeout': 60000,
        'attestation': 'direct',
    }

    return jsonify(publicKeyCredentialCreationOptions)

@app.route('/register/complete', methods=['POST'])
def register_complete():
    data = request.json
    username = data.get('username')
    credential = data.get('credential')

    if not username or not credential:
        return jsonify({'error': 'Invalid request data'}), 400

    # Get registration attempt data
    registration_data = cache.get(f'registration:{username}')
    if not registration_data:
        return jsonify({'error': 'No active registration attempt found'}), 400

    # Verify the credential
    if not credential.get('id') or not credential.get('response'):
        return jsonify({'error': 'Invalid credential format'}), 400

    credential_id = credential['id']
    
    # Check if this credential ID is already registered
    if cache.get(f'credential:{credential_id}'):
        return jsonify({'error': 'Credential already registered'}), 400

    # Parse and verify attestation object
    try:
        attestation_object = base64.urlsafe_b64decode(
            credential['response']['attestationObject'] + '=='
        )
        attestation_data = cbor2.loads(attestation_object)
        
        # Store the credential with device information
        credential_data = {
            'username': username,
            'public_key': credential['response']['attestationObject'],
            'device_fingerprint': registration_data['device_fingerprint'],
            'created_at': datetime.now().isoformat()
        }
        
        cache.set(f'credential:{credential_id}', credential_data)
        
        # Clean up registration attempt data
        cache.r.delete(f'registration:{username}')
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': f'Failed to verify attestation: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(host='localhost', port=3000)