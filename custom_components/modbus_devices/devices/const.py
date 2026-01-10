from enum import Enum

class ByteOrder(str, Enum):
    MSB = 'MSB'
    LSB = 'LSB'

class WordOrder(str, Enum):
    NORMAL = 'NORMAL'
    SWAP = 'SWAP'