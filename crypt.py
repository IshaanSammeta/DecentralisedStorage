from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode

# Encryption
def encrypt_ipfs_hash(ipfs_hash, key):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(ipfs_hash.encode())
    return b64encode(cipher.nonce + tag + ciphertext)

# Decryption
def decrypt_ipfs_hash(encrypted_hash, key):
    encrypted_data = b64decode(encrypted_hash)
    nonce = encrypted_data[:16]
    tag = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode()

# Example usage
encryption_key = get_random_bytes(16)  # Generate a 128-bit (16-byte) encryption key
ipfs_hash = "QmcDiYQXDNJkwu6bWhsHXpvWueJuywW35j42TQtcHiJYPM"

# Encrypt IPFS hash
encrypted_hash = encrypt_ipfs_hash(ipfs_hash, encryption_key)
print("Encrypted IPFS Hash:", encrypted_hash)

# Decrypt IPFS hash
decrypted_hash = decrypt_ipfs_hash(encrypted_hash, encryption_key)
print("Decrypted IPFS Hash:", decrypted_hash)
