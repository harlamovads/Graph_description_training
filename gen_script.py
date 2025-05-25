import secrets

# Generate two different random keys
secret_key = secrets.token_hex(32)
jwt_secret_key = secrets.token_hex(32)

print(f"SECRET_KEY={secret_key}")
print(f"JWT_SECRET_KEY={jwt_secret_key}")