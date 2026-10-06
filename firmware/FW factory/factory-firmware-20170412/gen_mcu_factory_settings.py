#!/usr/bin/python
import sys
import os
import struct
import time
import random
import hashlib
# https://raw.githubusercontent.com/necaris/cuid.py/master/cuid.py
import cuid
import sha

from functools import reduce

# cortex-m0 is little_endian
little_endian = True

def uniq_id():
    uniq_cuid = cuid.cuid()
    # sha1 of cuid that looks really random
    random_sn = sha.new(uniq_cuid).hexdigest()[0:28]

    # ed25519_privateKey[32];
    # improved random seeding
    random.seed()
    h = hashlib.sha224(''.join(os.uname())).hexdigest()
    seed = int((random.random() * 4000000)) + 810308 + int(h[0:7], 16)
    random.seed(seed)

    ed25519_privateKey = map(lambda a: random.getrandbits(8), range(0, 32))

    return {
        "cuid": uniq_cuid,
        "random_sn": random_sn,
        "ed25519_privateKey": ed25519_privateKey,
    }

def rawdata(
    u32_format_version, u32_hardware_version, u32_batch_production,
    capas,
    sharedkey_path,
    rsapublic_path,
    _uniq_id = uniq_id()):

    chunks = []
    chunks.append(struct.pack("<LLL", u32_format_version, u32_hardware_version, u32_batch_production))

    capa0 = 0xfc
    if not capas.get('HACK_BACKBUTTON_SWITCHED'):
        capa0 = capa0 | (1<<0)
    if not capas.get('HACK_HT1632_VERTICALLY_MIRRORED'):
        capa0 = capa0 | (1<<1)
    chunks.append(struct.pack("<B", capa0))

    #  uint8_t reserved0[64-13]; // future capabilities
    for k in range(13, 64):
        chunks.append(struct.pack("<B", 0xff))

    if False:
        chunks.append(_uniq_id['uniq_cuid']) # size 25
        # reserved1
        for k in range(0, 3):
            chunks.append(struct.pack("<B", 0xFF))
    else:
        chunks.append(_uniq_id['random_sn'])

    # ed25519_privateKey[32];
    #print(map(lambda r: '0x%02x'%(r), ed25519_privateKey))
    #print("".join(map(lambda r: '%02x'%(r), ed25519_privateKey)))
    chunks.append(bytearray(_uniq_id['ed25519_privateKey']))
    #struct.pack("<B", random.getrandbits(8)))

    # chacha20poly1305_sharedkey[32]
    chunks.append(struct.pack("<L", 0x00000000))
    sk_fo = open(sharedkey_path, "rb")
    sharedkey = sk_fo.read()
    sk_fo.close();
    chunks.append(sharedkey)

    # rsa_publickey[294]
    chunks.append(struct.pack("<L", 0x00000000))
    sk_fo = open(rsapublic_path, "rb")
    sharedkey = sk_fo.read()

    chunks.append(sharedkey)

    # reserved2 (512 - 128 - 294 - 8 - 28)
    for k in range(0, 512 - 128 - 294 - 8 - 28):
        chunks.append(struct.pack("<B", 0xff))

    # merge chunks
    data = reduce(lambda acc, ba: acc + ba, chunks, bytearray())

    return [data,  _uniq_id]
