import bcrypt

stored_hash = "$2b$12$JXzbLO5nSr.6HPpUeRHOuC"

password = "admin123"

try:
    correct_hash = "$2b$12$SJXzb6LOSnSr.6HPpUeRHOOuQsIR1gu8t/TIHXNKeZtuYAxex2bzE2"
    result = bcrypt.checkpw(password.encode('utf-8'), correct_hash.encode('utf-8'))
    print(f"Password 'admin123' with correct hash: {result}")
    
    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"\nFresh hash for 'admin123': {new_hash}")
    print(f"Verification: {bcrypt.checkpw(password.encode('utf-8'), new_hash.encode('utf-8'))}")
    
except Exception as e:
    print(f"Error: {e}")