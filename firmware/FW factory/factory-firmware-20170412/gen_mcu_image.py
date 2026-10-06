#!/usr/bin/env python
# python: 2.7
# modules required: intelhex
# author: F. Germain
# version:
# 1.0   2017-04-12, initial version

import sys
import os
from intelhex import IntelHex
from functools import reduce
import binascii
import gen_mcu_factory_settings
import json
import time
import datetime

if datetime.datetime.now() < datetime.datetime(2017, 4, 1, 0, 0, 0, 0):
    print("please set time on current PC or device")
    sys.exit(1)

def gen_image(out_filename):
    u32_format_version = 0

    u32_batch_production = int(batch_production)

    #capas = reduce(lambda acc, k: (acc.update({k: os.environ.get(k)}) or acc) if os.environ.get(k) else acc,
    #    [ 'HACK_BACKBUTTON_SWITCHED', 'HACK_HT1632_VERTICALLY_MIRRORED'],
    #    {})

    uniq_id = None
    readable_uniq_id = None

    if os.environ.get("DEVICE_UNIQ_ID_FILE"):
        # reload uniq id from a file
        info_file = os.environ.get("DEVICE_UNIQ_ID_FILE")
        with open(info_file,'r') as ifp:
            readable_uniq_id = json.loads(ifp.read())
        test =  list(bytearray(binascii.unhexlify(readable_uniq_id["ed25519_privateKey"])))
        uniq_id = {
            'cuid': str(readable_uniq_id["cuid"]),
            'random_sn': str(readable_uniq_id["random_sn"]),
            'ed25519_privateKey': map(long, list(bytearray(binascii.unhexlify(readable_uniq_id["ed25519_privateKey"])))),
        }
    else:
        uniq_id = gen_mcu_factory_settings.uniq_id()

        readable_uniq_id = {
            'cuid': uniq_id["cuid"],
            'random_sn': uniq_id["random_sn"],
            'ed25519_privateKey': binascii.hexlify(bytearray(uniq_id["ed25519_privateKey"])),
        }

    print(readable_uniq_id)

    facset_data, uniq_id = gen_mcu_factory_settings.rawdata(
        u32_format_version, u32_hardware_version, u32_batch_production,
        capas,
        sharedkey_path,
        rsapublic_path,
        uniq_id)

    # dump factory settings for device
    #with open(out_base_file + '.facset.bin', "wb") as fo:
    #    fo.write(facset_data)

    # test for stvp programmer software, but it's not working
    # arm-none-eabi-objcopy -I binary --change-addresses 0x1FFFF800 -O ihex device/firmware/$product/option_byte_protected.bin tmp
    # ( head -n -2 device/firmware/$product/kello_loader.hex; head -n -2 Output/private/$product/kello.app+sign.hex; head -n -2 tmp; echo :00000001FF; ) > $PACKAGE_NAME/$product-loader-${LOADER_VERSION}_app+sign-${MCU_APP_VERSION}_opt-protected.hex


    # files need to be concatenated at the same order as flash memory map
    # do not really need a strict order with IntelHex

    if product == "kello.0":
      files_to_concat = [
        IntelHex(app_hex_file),
        IntelHex(app_sign_hex_file),
        IntelHex(loader_hex_file),
        None # factory_settings
      ]
      factory_settings_ih = IntelHex()
      factory_settings_ih.frombytes(facset_data, 0x100e00)
      files_to_concat[3] = factory_settings_ih
    elif product == "kello.1":
      files_to_concat = [
        IntelHex(loader_hex_file),
        None, # factory_settings
        IntelHex(app_hex_file),
        IntelHex(app_sign_hex_file)
      ]
      factory_settings_ih = IntelHex()
      factory_settings_ih.frombytes(facset_data, 0x8003e00)
      files_to_concat[1] = factory_settings_ih
    else:
      print "need PRODUCT"
      sys.exit(1)


    def ihmerge(ihmerged, ih):
        #print ih.segments()
        # ignore start addresses
        ih.start_addr = None
        ihmerged.merge(ih, overlap='error')
        return ihmerged

    ihmerged = reduce(lambda acc, path: ihmerge(acc, path), files_to_concat, IntelHex())
    #print ihmerged.segments()

    with open(out_filename, 'w') as outfile:
        ihmerged.write_hex_file(outfile)

    return readable_uniq_id

if __name__ == "__main__":
    work_dir = sys.argv[1]

    if len(sys.argv) > 5:
        loader_hex_file = sys.argv[2]
        app_hex_file = sys.argv[3]
        app_sign_hex_file = sys.argv[4]

        sharedkey_path = sys.argv[5]
        rsapublic_path = sys.argv[6]

        batch_production = os.environ.get("BATCH_PRODUCTION")
    else:
        import ConfigParser  # changed to configparser in python 3

        batch_production = sys.argv[2]
        config = ConfigParser.ConfigParser()
        config.readfp(open("batch-%s/config.ini" % (batch_production)))

        product = config.get("INFO", "PRODUCT")

        loader_hex_file = "batch-%s/%s-mcu_loader-%s.hex" % (batch_production, product, config.get("INFO", "MCU_LOADER_VERSION"))
        app_hex_file = "batch-%s/%s-mcu_app-%s.hex" % (batch_production, product, config.get("INFO", "MCU_APP_VERSION"))
        app_sign_hex_file = "batch-%s/%s-mcu_app_sign-%s.hex" % (batch_production, product, config.get("INFO", "MCU_APP_VERSION"))

        sharedkey_path = "batch-%s/sharedkey_%s.bin" % (batch_production, config.get("INFO", "SHARED_KEY_ID"))
        rsapublic_path = "batch-%s/publickey_%s.bin" % (batch_production, config.get("INFO", "PUBLIC_KEY_ID"))

        hardware_version = config.get("INFO", "HARDWARE_VERSION")
        u32_hardware_version = int(hardware_version, 16)

        capas = {}
        capas["HACK_BACKBUTTON_SWITCHED"]=config.get("CAPABILITIES", "HACK_BACKBUTTON_SWITCHED")
        capas["HACK_HT1632_VERTICALLY_MIRRORED"]=config.get("CAPABILITIES", "HACK_HT1632_VERTICALLY_MIRRORED")

    out_base_file = "%s/latest_mcu_image-%s.hex" % (sys.argv[1], batch_production)
    readable_uniq_id = gen_image(out_base_file)

    if not os.environ.get("DEVICE_UNIQ_ID_FILE"):
        # dump uniq_id
        uniq_id_file = "%s/uniq_id-%s-%s.json" % (sys.argv[1], str(int(1000*time.time())), readable_uniq_id['random_sn'])
        print("generated uniq_id file %s" % (uniq_id_file))
        with open(uniq_id_file,'w') as ifp:
            ifp.write(json.dumps(readable_uniq_id))
