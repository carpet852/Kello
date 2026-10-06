#!/usr/bin/env python
# python: 2.7
# modules required: pyserial, colorama
# author: S.Carpentier
# version:
# 1.0   2017-04-10, initial version


ver_nfo = "1.0"

import os
import re
import time
import sys
import csv
import ConfigParser  # changed to configparser in python 3
import subprocess
#import multiprocessing
from colorama import init
from colorama import Fore, Back, Style
from Tkinter import Tk      # for clipboard functions
import msvcrt #MicroSoft Vitual C/C++ Runtime. For Windows O.S. only!
import serial
import traceback


#---------------------------------------------------------------------
# print color text in shell
# input:
#        text:            target to print
#        #fore_color:        text color        Accept color key word: RED,YELLOW,BLUE. NOT ACTIVATED NOW
#        back_color:        backgroud color    Accept color key word: RED,YELLOW,BLUE
#
#---------------------------------------------------------------------
def print_color(text,back_color="RED",fore_color="WHITE"):
    if back_color == "RED":
        print(Fore.WHITE + Back.RED + Style.BRIGHT + text)
    elif back_color == "YELLOW":
        print(Fore.WHITE + Back.YELLOW + Style.BRIGHT + text)
    elif back_color == "BLUE":
        print(Fore.WHITE + Back.BLUE + Style.BRIGHT + text)
    if back_color == "GREEN":
        print(Fore.WHITE + Back.GREEN + Style.BRIGHT + text)
    elif back_color == "MAGENTA":
        print(Fore.WHITE + Back.MAGENTA + Style.BRIGHT + text)
    elif back_color == "CYAN":
        print(Fore.WHITE + Back.CYAN + Style.BRIGHT + text)
    print(Fore.RESET + Back.RESET + Style.RESET_ALL)

#---------------------------------------------------------------------
# print message and add it to the log str
#---------------------------------------------------------------------
    
def print_log(str):
    global log_str
    print(str)
    log_str += str+"\r\n"

def printc_log(str,back_color="RED",fore_color="WHITE"):
    global log_str
    print_color(str,back_color,fore_color)
    log_str += str+"\r\n"
    

#---------------------------------------------------------------------
# read the config.ini file
#---------------------------------------------------------------------
def get_config(section,key):
    config = ConfigParser.ConfigParser()
    config.readfp(open("config.ini"))
    value = config.get(section,key)
    return value


#---------------------------------------------------------------------
# clear keyboard input
# Attention! Only for Windows
#---------------------------------------------------------------------
def flush_input():
    while msvcrt.kbhit():
        msvcrt.getch()


#----------------------------------------------
# clear keyboard input
# Attention! Only for Linux
#----------------------------------------------
#def flush_input():
#    sys.stdout.flush();
#    termios.tcflush(sys.stdin, termios.TCIOFLUSH)


#---------------------------------------------------------------------
# search specific patterns in a string
# keys: fw,mfgid,mac,rc,batt,adxl
#---------------------------------------------------------------------
def search_value(key,str,ref_str=""):
    if key == "mac":
        try:
            str2 = re.findall(ref_str,str)[0]
            p = re.compile('.*(?P<macstr>[0-9a-fA-F:]{17}).*')
            m = p.search(str2)
            if m == None:
                return False
            mac = m.group("macstr")
            return mac
        except IndexError:
            return False
    elif key == "string":
        i = re.search(ref_str,str)
        if i == None:
            return False
        else:
            return True
        #print i.groups()[0]
    else:
        return False


#---------------------------------------------------------------------
# search a MAC in a string and compare to the reference MAC
#---------------------------------------------------------------------
def compare_mac(mac,ref_mac):
    if mac == False:
        mac1 = "FFFFFFFFFFFF"
    else:
        mac1= mac.replace(":","").upper()
    if ref_mac == False:
        mac2 = "FFFFFFFFFFFF"
    else:
        mac2 = ref_mac.replace(":","").upper()
    if mac1 != mac2:
        mac_diff = 1
    else:
        mac_diff = 0
    return mac1, mac_diff

#---------------------------------------------------------------------
# verify MAC format
#---------------------------------------------------------------------
def check_mac(mac):
    mac_err=0
    if len(mac) != 12:
        mac_err=1
    else:
        try:
            i = re.search(r'([0-9A-Fa-f][0-9A-Fa-f])([0-9A-Fa-f][0-9A-Fa-f])([0-9A-Fa-f][0-9A-Fa-f])([0-9A-Fa-f][0-9A-Fa-f])([0-9A-Fa-f][0-9A-Fa-f])([0-9A-Fa-f][0-9A-Fa-f])', mac).groups()
        except AttributeError:
            mac_err=1
    return mac_err

                
#---------------------------------------------------------------------
# save data to txt logfile
#---------------------------------------------------------------------
def save_log(log,mac,path,sta,sta_no):
    today = time.strftime("20%y%m%d",time.localtime())
    hour_min_sec = time.strftime("%H%M%S",time.localtime())
    try:
        logfile_path = "%s\\kello_%s_%s_%s_%s_%s.txt"%(path,mac,sta,sta_no,today,hour_min_sec)
        logfile = open(logfile_path,"w")
        logfile.write(log)
        logfile.close()
    except IOError:
        printc_log("Cannot write "+logfile_path+" ERROR")
        printc_log("Check connection and retest MAC")


#---------------------------------------------------------------------
# save data to csv logfile
#---------------------------------------------------------------------
def save_csv(list,path):
    try:
        with open(path, "ab") as fwrite:
                writer = csv.writer(fwrite, quoting=csv.QUOTE_MINIMAL)
                writer.writerow(list)
    except IOError:
        printc_log("Cannot connect to "+path+" ERROR")
        printc_log("Check connection and retest MAC")


#---------------------------------------------------------------------
# send command+ENTER to Libre UART
# inputs:
#   - uart: port name
#   - cmd: ascii string, followed by ENTER
#---------------------------------------------------------------------
def send_uart(uart,cmd):
    if len(cmd) != 0:
        for i in range(len(cmd)):
            x = cmd[i]
            uart.write(x)
            time.sleep(0.001)
        uart.write("\r")
    else:    # if cmd = '', send ENTER
        uart.write("\r")
        
#---------------------------------------------------------------------
# send command to MCU UART
# inputs:
#   - uart: port name
#   - cmd: ascii string
#---------------------------------------------------------------------
# http://stackoverflow.com/questions/5901706/the-bytes-type-in-python-2-7-and-pep-358
# http://stackoverflow.com/questions/24409581/do-python-strings-end-in-a-terminating-null
def send_mcu_uart(uart,cmd):
    #print len(cmd)
    if len(cmd) != 0:
        for i in range(len(cmd)):
            x = cmd[i]
            uart.write(x)
            time.sleep(0.001)
    else:
        pass     

#---------------------------------------------------------------------------
# get trace from Libre UART after command is sent
# inputs:
#       - uart: port name
#       - cmd: ascii string, if left empty get trace from uart buffer
#       - delay: delay in sec btw send and receive
#       - nbtry: number of read iterations
#       - bps: uart speed in baud
#       - bufsize: uart buffer size in byte
# outputs:
#       - buf: string
#       - err: error flag
#---------------------------------------------------------------------------
# http://stackoverflow.com/questions/12302155/how-to-expand-input-buffer-size-of-pyserial
def get_uart(uart,cmd,delay,nbtry,bps,bufsize):
    buf = ""
    err=0
    fullbuftime = bufsize*8/float(bps)
    #print fullbuftime
    try:
        if cmd != "":
            send_uart(uart,"\r") #ENTER
            time.sleep(0.5)
            uart.flushInput()  #clear UART read buffer
            uart.flushOutput()
            send_uart(uart,cmd)
            time.sleep(0.5)
        i = nbtry
        while(i>0):
            temp = ''
            countdw = delay
            while countdw > 0:
                time.sleep(fullbuftime)
                temp += uart.read(uart.inWaiting())  # inWaiting() returns the nb of bytes received
                countdw = countdw - fullbuftime
            #print temp
            try:
                buf += str(temp.decode("ascii","ignore"))   # decode sequence of bytes and ignore non-ascii characters
            except:
                err=1
                break   #terminates the current loop and resumes execution after the loop
            i = i-1
    except:
        #buf = sys.exc_info()
        buf = traceback.format_exc()
        err=1
    return buf,err

#---------------------------------------------------------------------------
# get trace from MCU UART after command is sent
# inputs:
#       - uart: port name
#       - cmd: ascii string, if left empty get trace from uart buffer
#       - delay: btw send and receive in sec
#       - nbtry: number of read iterations
# outputs:
#       - buf: string
#       - err: error flag
#---------------------------------------------------------------------------
def get_mcu_uart(uart,cmd,delay,nbtry):
    buf = ""
    err=0
    try:
        if cmd != "":
            send_mcu_uart(uart,"\r") #ENTER
            time.sleep(0.5)
            uart.flushInput()  #clear UART read buffer
            uart.flushOutput()
            send_mcu_uart(uart,cmd)
            time.sleep(0.5)
        i = nbtry
        while(i>0):
            time.sleep(delay)
            temp = uart.read(uart.inWaiting())  # inWaiting() returns the nb of bytes received
            #print temp
            try:
                buf += str(temp.decode("ascii","ignore"))   # decode sequence of bytes and ignore non-ascii characters
            except:
                err=1
                break   #terminates the current loop and resumes execution after the loop
            i = i-1
    except:
        #buf = sys.exc_info()
        buf = traceback.format_exc()
        err=1
    return buf,err
    

#---------------------------------------------------------------------
# config
#---------------------------------------------------------------------

log_path = get_config("INFO","LOG_PATH")
factory_nfo = get_config("INFO","FACTORY")
sta_nfo = get_config("INFO","STATION")
stano_nfo = get_config("INFO","STATION_NO")

uart_buf_size = int(get_config("UART","UART_BUF_SIZE"))

uart_mcu_port = int(get_config("UART","MCU_COM_PORT"))
uart_mcu_baudrate = int(get_config("UART","MCU_COM_BAUDRATE"))
uart_mcu_parity = get_config("UART","MCU_COM_PARITY")
uart_mcu_stopbit = int(get_config("UART","MCU_COM_STOPBIT"))
fw_mcu_flag = int(get_config("FIRMWARE","MCU_FW_UPGRADE"))
fw_mcu_cmd = get_config("FIRMWARE","MCU_FW_FLASH_TOOL")+" "+get_config("FIRMWARE","MCU_FW_FLASH_ARG").replace('$',get_config("FIRMWARE","MCU_FW_FILE"))
fw_mcu_str = get_config("FIRMWARE","MCU_FW_FLASH_STR")

uart_libre_port = int(get_config("UART","LIBRE_COM_PORT"))
uart_libre_baudrate = int(get_config("UART","LIBRE_COM_BAUDRATE"))
uart_libre_parity = get_config("UART","LIBRE_COM_PARITY")
uart_libre_stopbit = int(get_config("UART","LIBRE_COM_STOPBIT"))
fw_libre_flag = int(get_config("FIRMWARE","LIBRE_FW_UPGRADE"))
fw_libre_cmd = get_config("FIRMWARE","LIBRE_FW_FLASH_CMD")
fw_libre_str = get_config("FIRMWARE","LIBRE_FW_FLASH_STR")
fw_libre_timeout = int(get_config("FIRMWARE","LIBRE_FW_FLASH_TIMEOUT"))

macscan_flag = int(get_config("TEST","MAC_SCAN"))
hellochk_flag = int(get_config("TEST","MCU_HELLO_CHECK"))
hellochk_cmd = '\n'+get_config("TEST","MCU_HELLO_CHECK_CMD")+'\r'   # do not add '\n' and '\r' characters in the config.ini as they will not be interpreted
hellochk_str = get_config("TEST","MCU_HELLO_CHECK_STR")
macmemchk_flag = int(get_config("TEST","LIBRE_MACMEM_CHECK"))
macmemchk_cmd = get_config("TEST","LIBRE_MACMEM_CHECK_CMD")
macmemchk_str = get_config("TEST","LIBRE_MACMEM_CHECK_STR")
usbchk_flag = int(get_config("TEST","LIBRE_USB_CHECK"))
usbchk_cmd = get_config("TEST","LIBRE_USB_CHECK_CMD")
usbchk_str = get_config("TEST","LIBRE_USB_CHECK_STR")

pass_ind = "PASS"
fail_ind = "FAIL"
notapp_ind = "N/A"

test_count = usbchk_flag + macmemchk_flag + fw_libre_flag + fw_mcu_flag + hellochk_flag

#---------------------------------------------------------------------
# config end
#---------------------------------------------------------------------


csvhdr_list = ["station","station number","station result","mac","start time", "duration"]
for i in range(0, test_count):
    csvhdr_list.append("test item")
    csvhdr_list.append("value")
    csvhdr_list.append("range")
    csvhdr_list.append("result")



# colorama init
init()

# global variable to store the logs
log_str = ""

def main():

    loop_flag = 1
    
    while(loop_flag):
        
        global log_str  # needed to modify a global variable inside a function
        csvdata_list = []
        
        #os.system('clear')     # clear screen -linux
        os.system("cls")        # clear screen -win

        print_log("KELLO Factory Test Tool ver "+ver_nfo+"\r\n")
        print_log("Station: "+sta_nfo)
        print_log("Station No: "+stano_nfo+"\r\n")
        
        if macscan_flag:
            disp_str = "Scan MAC address label...\r\n"
            log_str = disp_str
            mac_scan = raw_input(disp_str)  # 'input' cmd takes only Python expressions
        else:
            disp_str = "MAC address not scanned\r\n"
            log_str = ""
            print_log(disp_str)
            key_val = raw_input("Press any key...\r\n")
        
        day = time.strftime("20%y%m%d",time.localtime())
        folder_path=log_path+"\\"+day
        csv_path = folder_path+"\\"+"kello"+"_"+factory_nfo+"_"+sta_nfo+"_"+stano_nfo+"_"+day+".csv"
        
        # create the folder if it does not exist
        try:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
        except WindowsError:
            print_color("[ERROR] Cannot connect to "+folder_path)
            os.system("pause")
            continue    # returns to the beginning of the while loop
        
        # create the csv file if it does not exist
        if not os.path.isfile(csv_path):
            with open(csv_path, "wb") as fwrite:
                writer = csv.writer(fwrite, delimiter=',')
                writer.writerow(csvhdr_list)

        mac_mem = "FFFFFFFFFFFF"

        if macscan_flag:
            if check_mac(mac_scan):
                print_color("[ERROR] MAC format")
                while(True):
                    key_val = raw_input("Press ENTER to continue...")
                    if key_val == "":   # ENTER returns ""
                        break
                continue    # returns to the beginning of the while loop
        else:
            mac_scan = "FFFFFFFFFFFF"
        log_str += mac_scan+"\r\n"

        time_scan = time.strftime("20%y%m%dt%H%M%S",time.localtime())
        time_begin = time.time()

        # ["station","station number","station result","mac","start time", "duration"]
        csvdata_list.extend((sta_nfo, stano_nfo, pass_ind, mac_scan, time_scan, "0"))
        csvstares_col = 2
        csvdura_col = 5
        
            
        # ------------------------- Configure Libre COM port
        if fw_libre_flag or usbchk_flag or macmemchk_flag:
            disp_str = "power KELLO and wait 15 sec for product to boot..."
            print_log(disp_str)
            disp_str = "Libre COM port setting..."
            print_log(disp_str)
            uart1 = serial.Serial()
            uart1.port = uart_libre_port-1
            uart1.baudrate = uart_libre_baudrate
            uart1.parity = uart_libre_parity
            uart1.stopbits = uart_libre_stopbit
            uart1.timeout = 0.5
            if(uart1.isOpen()):
                uart1.close()
            try:
                uart1.open()
            except serial.SerialException:
                disp_str = "[ERROR] Libre COM port failure"
                printc_log(disp_str)
                save_log(log_str,mac_scan,folder_path,sta_nfo,stano_nfo)
                os.system("pause")
                continue    # returns to the beginning of the while loop
            disp_str = "[PASS] Libre COM port open"
            printc_log(disp_str,"GREEN","GREEN")
            flush_input() #flush serial input buffer
        
        # ------------------------- USB check
        if usbchk_flag:
            uart1_buf, uart1_err = get_uart(uart1,usbchk_cmd,0.1,1,uart_libre_baudrate,uart_buf_size)
            print_log (uart1_buf)

            test_name = "usb image chk"
            test_value = ""
            test_range = usbchk_str
            test_result = fail_ind
            
            x = search_value("string",uart1_buf,usbchk_str)
            if not x:
                disp_str = "[ERROR] Libre image not found or USB stick not mounted"
                printc_log(disp_str)
                test_result = fail_ind
                save_log(log_str,mac_scan,folder_path,sta_nfo,stano_nfo)
                csvdata_list.extend((test_name, test_value, test_range, test_result))
                csvdata_list[csvstares_col] = fail_ind
                save_csv(csvdata_list,csv_path)
                os.system("pause")
                continue    # returns to the beginning of the while loop
            else:
                disp_str = "[PASS] Libre image found on USB stick"
                printc_log(disp_str,back_color="GREEN",fore_color="GREEN")
                test_value = usbchk_str
                test_result = pass_ind
                csvdata_list.extend((test_name, test_value, test_range, test_result))
        
        # ------------------------- MAC memory check
        if macmemchk_flag:
            uart1_buf, uart1_err = get_uart(uart1,macmemchk_cmd,0.1,1,uart_libre_baudrate,uart_buf_size)
            print_log (uart1_buf)

            test_name = "mac mem chk"
            test_value = ""
            test_range = mac_scan
            test_result = fail_ind
            
            x = search_value("mac",uart1_buf,macmemchk_str)
            mac_mem, mac_error = compare_mac(x,mac_scan)
            print_log("mac in memory: " + mac_mem)
            print_log("mac scanned: " + mac_scan)
            test_value = mac_mem

            if mac_error == 1:
                disp_str = "[ERROR] MAC check fail"
                printc_log(disp_str)
                save_log(log_str,mac_scan,folder_path,sta_nfo,stano_nfo)
                csvdata_list.extend((test_name, test_value, test_range, test_result))
                csvdata_list[csvstares_col] = fail_ind
                save_csv(csvdata_list,csv_path)
                os.system("pause")
                continue    # returns to the beginning of the while loop
            else:
                disp_str = "[PASS] MAC check OK"
                printc_log(disp_str,back_color="GREEN",fore_color="GREEN")
                test_result = pass_ind
                csvdata_list.extend((test_name, test_value, test_range, test_result))
        
        # ------------------------- Libre FW upgrade
        if fw_libre_flag:
            disp_str = "Libre FW upgrade: wait for %s sec..."%fw_libre_timeout
            print_log(disp_str)
            disp_str = "See progress bar on LED display: U %"
            print_log(disp_str)
            test_name = "libre fw upgrade"
            test_value = notapp_ind
            test_range = notapp_ind
            test_result = fail_ind
            
            uart1_buf, uart1_err = get_uart(uart1,fw_libre_cmd,fw_libre_timeout,1,uart_libre_baudrate,uart_buf_size)
            print_log(uart1_buf)
            x = search_value("string",uart1_buf,fw_libre_str)
            if not x:
                disp_str = "[ERROR] Libre FW upgrade FAIL"
                printc_log(disp_str)
                test_result = fail_ind
                save_log(log_str,mac_scan,folder_path,sta_nfo,stano_nfo)
                csvdata_list.extend((test_name, test_value, test_range, test_result))
                csvdata_list[csvstares_col] = fail_ind
                save_csv(csvdata_list,csv_path)
                os.system("pause")
                continue    # returns to the beginning of the while loop
            else:
                disp_str = "[PASS] Libre FW upgrade OK"
                printc_log(disp_str,back_color="GREEN",fore_color="GREEN")
                test_result = pass_ind
                csvdata_list.extend((test_name, test_value, test_range, test_result))
                
            
        # ------------------------- MCU FW upgrade
        if fw_mcu_flag:
            disp_str = "STM32 FW upgrade..."
            print_log(disp_str)
            test_name = "mcu fw upgrade"
            test_value = notapp_ind
            test_range = notapp_ind
            test_result = fail_ind
            try:
                disp_str = fw_mcu_cmd
                print_log(disp_str)
                # http://stackoverflow.com/questions/24904945/command-prompt-error-c-program-is-not-recognized-as-an-internal-or-external-c
                # http://stackoverflow.com/questions/4514751/pipe-subprocess-standard-output-to-a-variable
                out = subprocess.check_output(fw_mcu_cmd)  # Run command with arguments and return its output as a byte string
                print_log(out)
                x = search_value("string",out,fw_mcu_str)
                if not x:
                    disp_str = "[ERROR] ST-Link FW programming fail"
                    printc_log(disp_str)
                    save_log(log_str,mac_scan,folder_path,sta_nfo,stano_nfo)
                    csvdata_list.extend((test_name, test_value, test_range, test_result))
                    csvdata_list[csvstares_col] = fail_ind
                    save_csv(csvdata_list,csv_path)
                    os.system("pause")
                    continue    # returns to the beginning of the while loop
                else:
                    disp_str = "[PASS] ST-Link FW programming OK"
                    printc_log(disp_str,back_color="GREEN",fore_color="GREEN")
                    test_result = pass_ind
                    csvdata_list.extend((test_name, test_value, test_range, test_result))
            except subprocess.CalledProcessError as e:
                ret_str = e.output
                print_log(ret_str)
                disp_str = "[ERROR] ST-Link programming command error"
                printc_log(disp_str)
                save_log(log_str,mac_scan,folder_path,sta_nfo,stano_nfo)
                csvdata_list.extend((test_name, test_value, test_range, test_result))
                csvdata_list[csvstares_col] = fail_ind
                save_csv(csvdata_list,csv_path)
                os.system("pause")
                continue    # returns to the beginning of the while loop
            time.sleep(1) # The ST-Link freezes the uart during FW prog and a reset is needed after
        
        # ------------------------- MCU hello check
        if hellochk_flag:
            
            # ------------------------- Configure MCU COM port
            disp_str = "STM32 COM port setting..."
            print_log(disp_str)
            uart2 = serial.Serial()
            uart2.port = uart_mcu_port-1
            uart2.baudrate = uart_mcu_baudrate
            uart2.parity = uart_mcu_parity
            uart2.stopbits = uart_mcu_stopbit
            uart2.timeout = 0.5
            if(uart2.isOpen()):
                uart2.close()
            try:
                uart2.open()
            except serial.SerialException:
                disp_str = "[ERROR] STM32 COM port failure"
                printc_log(disp_str)
                save_log(log_str,mac_scan,folder_path,sta_nfo,stano_nfo)
                os.system("pause")
                continue    # returns to the beginning of the while loop
            disp_str = "[PASS] STM32 COM port open"
            printc_log(disp_str,"GREEN","GREEN")
            flush_input() #flush serial input buffer
            
            # ------------------------- MCU hello check
            uart2_buf, uart2_err = get_mcu_uart(uart2,hellochk_cmd,0.1,1)
            #print uart2_err
            print_log(uart2_buf)
            test_name = "mcu hello chk"
            test_value = ""
            test_range = hellochk_str
            test_result = fail_ind
            
            #hello cmd: device_friendly_name, product_id, hardware_version, device_serial, firmware_version, libre_firmware_version, mcu_loader_version, bt_mac_address
            
            x = search_value("string",uart2_buf,hellochk_str)
            if not x:
                disp_str = "[ERROR] MCU hello cmd fail"
                printc_log(disp_str)
                test_value = ""
                test_result = fail_ind
                save_log(log_str,mac_scan,folder_path,sta_nfo,stano_nfo)
                csvdata_list.extend((test_name, test_value, test_range, test_result))
                csvdata_list[csvstares_col] = fail_ind
                save_csv(csvdata_list,csv_path)
                os.system("pause")
                continue    # returns to the beginning of the while loop
            else:
                uart_str = uart2_buf.replace("\0"," ")
                uart_list = uart_str.split('\r')
                #print uart_list
                info_str = uart_list[2]
                disp_str = "[PASS] MCU hello cmd OK"
                printc_log(disp_str,back_color="GREEN",fore_color="GREEN")
                test_value = info_str
                test_result = pass_ind
                csvdata_list.extend((test_name, test_value, test_range, test_result))
            

        # ------------------------- Save logfile
        time_end = time.time()
        time_total = round((time_end - time_begin),2)
        csvdata_list[csvdura_col] = str(time_total)
        save_log(log_str,mac_scan,folder_path,sta_nfo,stano_nfo)
        save_csv(csvdata_list,csv_path)
        
        if loop_flag:
            os.system("pause")



if __name__ == "__main__":
        main()

sys.exit(1)