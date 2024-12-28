import redis
import json

class RedisCache:
    def __init__(self):
        self.r = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True,
            username="default",
            # password="lwP4oIeR6bnrzKioTYCfwNOvw9FSBW31"
        )

    def get_all_keys(self):
        try:
            keys = self.r.keys('*')
            return keys
        except redis.RedisError as e:
            print(f"Error fetching keys: {e}")
            return []

    def get_value(self, key: str):
        try:
            data = self.r.get(key)
            return json.loads(data) if data else None
        except redis.RedisError as e:
            print(f"Error fetching value for key {key}: {e}")
            return None

# Initialize Redis cache
cache = RedisCache()

# Fetch all keys
keys = cache.get_all_keys()

# Print all keys and their values
for key in keys:
    value = cache.get_value(key)
    print(f"Key: {key}, Value: {json.dumps(value, indent=2)}")