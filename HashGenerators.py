import hashlib

# Hash generators for different algorithms

#TODO: Delete CRC32Generator
#TODO: Implement a SHA512Generator

class MD5Generator:

    @staticmethod
    def hashFile(data: str):
        return hashlib.md5(data.encode()).hexdigest()

class SHA256Generator:

    @staticmethod
    def hashFile(data: str):
        return hashlib.sha256(data.encode()).hexdigest()

class CRC32Generator:
    
    @staticmethod
    def hashFile(data: str):
        return hashlib.crc32(data.encode()).hexdigest()