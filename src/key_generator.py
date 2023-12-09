import ecdsa
import hashlib
import base58

def generate_key_pair():
    # Generate a random private key
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)

    # Get the corresponding public key
    public_key = private_key.get_verifying_key()

    return private_key, public_key

def public_key_to_address(public_key):
    # Perform SHA-256 hashing on the public key
    sha256_hash = hashlib.sha256(public_key.to_string()).digest()

    # Perform RIPEMD-160 hashing on the SHA-256 hash
    ripemd160_hash = hashlib.new('ripemd160')
    ripemd160_hash.update(sha256_hash)
    ripemd160_hash = ripemd160_hash.digest()

    # Add version byte (0x00 for Bitcoin mainnet)
    versioned_ripemd160_hash = b'\x00' + ripemd160_hash

    # Perform double SHA-256 hashing on the versioned hash
    checksum = hashlib.sha256(hashlib.sha256(versioned_ripemd160_hash).digest()).digest()

    # Append the first 4 bytes of the double hash as a checksum
    binary_address = versioned_ripemd160_hash + checksum[:4]

    # Convert the binary address to Base58
    bitcoin_address = base58.b58encode(binary_address).decode('utf-8')

    return bitcoin_address
