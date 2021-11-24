# Предпоследний параметр в конфигураторе играет роль!

import serial
import serial.tools.list_ports
import time
import struct
import FloatToHex, cgi, sys, math
import binascii

def serial_ports():
    ports = serial.tools.list_ports.comports()
    result = []
    event = 1
    for port, desc, hwid in sorted(ports):
        try:
            if (desc.find('CP') != -1):
                # print("{}: {}".format(port, desc, hwid))
                result.append(port)
                s = serial.Serial(port)
                s.close()
        except (OSError, serial.SerialException):
            pass
    return result

register_names = {"interface": 0x01, "tsmask": 0x02, "offset": 0x03, "pw1u": 0x04,
                  "pw2u": 0x05, "btru": 0x06, "outi": 0x07, "charge": 0x08, "ten": 0x09,
                  "sensors": 0x0A, "readsensor": 0x0B, "select_pwr": 0x0C, "ty": 0x0D,
                  "error_pwr": 0x0E, "ubatlow": 0x0F, "offsetinzero": 0x10, "offset_i": 0x11,
                  "calib_i": 0x12, "versions": 0x18, "current_param": 0x32, "serial_number": 0x33}

registers_pointer = {
    0x01: {"InterfaceAdress": 0x01, "InterfaceSpeed": 0x02, "InterfaceChet": 0x03, "ProtocolType": 0x04},
    0x02: {"TsMask1": 0x01, "TsMask2": 0x02, "TsMask3": 0x03, "TiMask1": 0x04, "TiMask2": 0x05, "TiMask3": 0x06},
    0x03: {"Offset101Ts": 0x01, "Offset101Ti": 0x02, "Offset101Ty": 0x03, "Offset101Tii": 0x04, "Hueta": 0x05},
    0x04: {"pw1_u_nom": 0x01, "pw1_u_max": 0x02, "pw1_u_min": 0x03, "pw1_u_max_hyst": 0x04, "pw1_u_min_hyst": 0x05},
    0x05: {"pw2_u_nom": 0x01, "pw2_u_max": 0x02, "pw2_u_min": 0x03, "pw2_u_max_hyst": 0x04, "pw2_u_min_hyst": 0x05},
    0x06: {"btr_u_nom": 0x01, "btr_u_max": 0x02, "btr_u_min": 0x03, "btr_u_max_hyst": 0x04, "btr_u_min_hyst": 0x05},
    0x07: {"out_i_1": 0x01, "out_i_2": 0x02},
    0x08: {"charge_err_min": 0x01, "charge_u_max": 0x02, "charge_u_min": 0x03, "charge_i_stable": 0x04,
           "charge_u_stable": 0x05},
    0x09: {"limit_ten": 0x01, "sensor_select": 0x02, "ten_or_fan": 0x03, "heat_for_load": 0x04},
    0x0A: {"sensor_t1": 0x01, "sensor_t2": 0x02, "sensor_t3": 0x03, "sensor_t4": 0x04, "sensor_t5": 0x05},
    0x0B: {"read_id_t1": 0x01, "read_id_t2": 0x02, "read_id_t3": 0x03, "read_id_t4": 0x04, "read_id_t5": 0x05},
    0x0C: {"select_pw": 0x01},
    0x0D: {"tu": 0x01},
    0x0E: {"error_pwr": 0x01},
    0x0F: {"u_bat_low_set": 0x01, "u_bat_low_hyst": 0x02},
    0x10: {"offset_in_zero": 0x01, "memory_how_offset": 0x02},
    0x11: {"offset_i1": 0x01, "offset_i2": 0x02},
    0x12: {"calib_i1": 0x01, "calib_i2": 0x02},
    0x18: {"bv_major": 0x01, "bv_minor": 0x02, "sv_major": 0x03, "sv_minor": 0x04, "sv_patch": 0x05, "sv_build": 0x06,
           "dev_type": 0x07},
    0x32: {"current_param": 0x01},
    0x33: {"serial_number": 0x01}
}

HIBYTE = b'\
\x00\xC0\xC1\x01\xC3\x03\x02\xC2\xC6\x06\x07\xC7\x05\xC5\xC4\x04\
\xCC\x0C\x0D\xCD\x0F\xCF\xCE\x0E\x0A\xCA\xCB\x0B\xC9\x09\x08\xC8\
\xD8\x18\x19\xD9\x1B\xDB\xDA\x1A\x1E\xDE\xDF\x1F\xDD\x1D\x1C\xDC\
\x14\xD4\xD5\x15\xD7\x17\x16\xD6\xD2\x12\x13\xD3\x11\xD1\xD0\x10\
\xF0\x30\x31\xF1\x33\xF3\xF2\x32\x36\xF6\xF7\x37\xF5\x35\x34\xF4\
\x3C\xFC\xFD\x3D\xFF\x3F\x3E\xFE\xFA\x3A\x3B\xFB\x39\xF9\xF8\x38\
\x28\xE8\xE9\x29\xEB\x2B\x2A\xEA\xEE\x2E\x2F\xEF\x2D\xED\xEC\x2C\
\xE4\x24\x25\xE5\x27\xE7\xE6\x26\x22\xE2\xE3\x23\xE1\x21\x20\xE0\
\xA0\x60\x61\xA1\x63\xA3\xA2\x62\x66\xA6\xA7\x67\xA5\x65\x64\xA4\
\x6C\xAC\xAD\x6D\xAF\x6F\x6E\xAE\xAA\x6A\x6B\xAB\x69\xA9\xA8\x68\
\x78\xB8\xB9\x79\xBB\x7B\x7A\xBA\xBE\x7E\x7F\xBF\x7D\xBD\xBC\x7C\
\xB4\x74\x75\xB5\x77\xB7\xB6\x76\x72\xB2\xB3\x73\xB1\x71\x70\xB0\
\x50\x90\x91\x51\x93\x53\x52\x92\x96\x56\x57\x97\x55\x95\x94\x54\
\x9C\x5C\x5D\x9D\x5F\x9F\x9E\x5E\x5A\x9A\x9B\x5B\x99\x59\x58\x98\
\x88\x48\x49\x89\x4B\x8B\x8A\x4A\x4E\x8E\x8F\x4F\x8D\x4D\x4C\x8C\
\x44\x84\x85\x45\x87\x47\x46\x86\x82\x42\x43\x83\x41\x81\x80\x40'

LOBYTE = b'\
\x00\xC1\x81\x40\x01\xC0\x80\x41\x01\xC0\x80\x41\x00\xC1\x81\x40\
\x01\xC0\x80\x41\x00\xC1\x81\x40\x00\xC1\x81\x40\x01\xC0\x80\x41\
\x01\xC0\x80\x41\x00\xC1\x81\x40\x00\xC1\x81\x40\x01\xC0\x80\x41\
\x00\xC1\x81\x40\x01\xC0\x80\x41\x01\xC0\x80\x41\x00\xC1\x81\x40\
\x01\xC0\x80\x41\x00\xC1\x81\x40\x00\xC1\x81\x40\x01\xC0\x80\x41\
\x00\xC1\x81\x40\x01\xC0\x80\x41\x01\xC0\x80\x41\x00\xC1\x81\x40\
\x00\xC1\x81\x40\x01\xC0\x80\x41\x01\xC0\x80\x41\x00\xC1\x81\x40\
\x01\xC0\x80\x41\x00\xC1\x81\x40\x00\xC1\x81\x40\x01\xC0\x80\x41\
\x01\xC0\x80\x41\x00\xC1\x81\x40\x00\xC1\x81\x40\x01\xC0\x80\x41\
\x00\xC1\x81\x40\x01\xC0\x80\x41\x01\xC0\x80\x41\x00\xC1\x81\x40\
\x00\xC1\x81\x40\x01\xC0\x80\x41\x01\xC0\x80\x41\x00\xC1\x81\x40\
\x01\xC0\x80\x41\x00\xC1\x81\x40\x00\xC1\x81\x40\x01\xC0\x80\x41\
\x00\xC1\x81\x40\x01\xC0\x80\x41\x01\xC0\x80\x41\x00\xC1\x81\x40\
\x01\xC0\x80\x41\x00\xC1\x81\x40\x00\xC1\x81\x40\x01\xC0\x80\x41\
\x01\xC0\x80\x41\x00\xC1\x81\x40\x00\xC1\x81\x40\x01\xC0\x80\x41\
\x00\xC1\x81\x40\x01\xC0\x80\x41\x01\xC0\x80\x41\x00\xC1\x81\x40'

def write_modbus(frame):
    data = [0x01, 0x17, 0x40, 0x55, 0x00, 0x04, 0x40, 0xAA, 0x00, 0x04]
    data.append(frame[3])
    for f in frame:
        data.append(f)
    hi,lo = crc16(data)
    data.append(hi)
    data.append(lo)
    return data

def crc16(data):
    crchi = 0xFF
    crclo = 0xFF
    index = 0

    for byte in data:
        index = crchi ^ int(byte)
        crchi = crclo ^ LOBYTE[index]
        crclo = HIBYTE[index]
    # print("{0:02X} {1:02X}".format(crclo, crchi)),
    return crchi, crclo
# Просто кидать нули вместо данных в посылке! А может и нет!
class ReadParam:

    # key в виде конкретного номера регистра номера байт управления уже передан добавить param как и везде
    def network_settings(self,param,key,value):
        frame = [0x55, 0xAA]
        frame.append(param)
        if (key == 0x01):
            frame.append(0x07)
            frame.append(0x01)
            frame.append(value)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame
        if (key == 0x02):
            frame.append(0x08)
            frame.append(0x02)
            if (value == 2400):
                frame.append(0x18)
                frame.append(0x00)
            if (value == 4800):
                frame.append(0x30)
                frame.append(0x00)
            if (value == 9600):
                frame.append(0x60)
                frame.append(0x00)
            if (value == 19200):
                frame.append(0xC0)
                frame.append(0x00)
            if (value == 38400):
                frame.append(0x80)
                frame.append(0x01)
            if (value == 57600):
                frame.append(0x40)
                frame.append(0x02)
            if (value == 115200):
                frame.append(0x80)
                frame.append(0x04)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame
        if (key == 0x03):
            frame.append(0x07)
            frame.append(0x03)
            if (value == "no"):
                frame.append(0x00)
            if (value == "even"):
                frame.append(0x01)
            if (value == "odd"):
                frame.append(0x02)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame
        if (key == 0x04):
            frame.append(0x07)
            frame.append(0x04)
            if (value == "modbus"):
                frame.append(0x01)
            if (value == "iec101"):
                frame.append(0x02)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame
        print("nothing is read!")
    # param в виде байта управления key в виде конкретного регистра
    def power_management(self,param, key, value):
        frame = [0x55, 0xAA]
        if (param == 0x0C):
            frame.append(0x0C)
            frame.append(0x08)
            frame.append(0x01)
            if (param == 0x00):
                frame.append(0x00)
            if (param == 0x01):
                frame.append(0x01)
            frame.append(0x00)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame

        if (param == 0x04 or param == 0x05 or param == 0x06 or param == 0x07 or param == 0x08 or param == 0x09):
            frame.append(param)
            frame.append(0x0A)
            frame.append(key)
            data = float_to_hex(value)
            for d in data:
                frame.append(d)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame
            print("power management is read!")

    def sensor_controls(self,param, key, value):
        frame = [0x55, 0xAA]
        if (param == 0x09 and key == 0x03):
            frame.append(0x09)
            frame.append(0x08)
            frame.append(0x03)
            if (value == "ten"):
                frame.append(0x00)
            if (value == "fan"):
                frame.append(0x01)
            frame.append(0x00)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame

        if (param == 0x09 and key == 0x02):
            frame.append(0x09)
            frame.append(0x08)
            if (key == 0x04 and value == "on"):
                frame.append(0x04)
                frame.append(0x01)
            else:
                frame.append(0x02)
                frame.append(value)
            frame.append(0x00)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame

        if (param == 0x0B):
            frame.append(0x0B)
            frame.append(0x07)
            frame.append(key)
            frame.append(value)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame

        if (param == 0x8A):
            frame.append(0x8A)
            frame.append(0x0E)
            frame.append(key)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame

    def serial_number(self,value):
        frame = [0x55, 0xAA, 0x33, 0x09]
        temp = []
        while value > 0:
            byte = value % 0x100
            temp.append(byte)
            value //= 0x100
        while len(temp) < 4:
            temp.append(0x00)
        frame.append(temp[0])
        frame.append(temp[1])
        frame.append(temp[2])
        frame.append(temp[3])
        crc = self.crc_calculate(frame)
        frame.append(crc)
        return frame

    def crc_calculate(self,frame):
        i = 2
        crc = 0x00
        while i < len(frame):
            crc = crc + frame[i]
            i = i + 1
        while crc > 256:
            crc = crc - 256
        return crc

class WriteParam:

    # key в виде конкретного номера регистра номера байт управления уже передан
    def network_settings(self,key,value):
        frame = [0x55, 0xAA]
        frame.append(0x01)
        if (key == 0x01):
            frame.append(0x07)
            frame.append(0x01)
            frame.append(value)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame
        if (key == 0x02):
            frame.append(0x08)
            frame.append(0x02)
            if (value == 2400):
                frame.append(0x18)
                frame.append(0x00)
            if (value == 4800):
                frame.append(0x30)
                frame.append(0x00)
            if (value == 9600):
                frame.append(0x60)
                frame.append(0x00)
            if (value == 19200):
                frame.append(0xC0)
                frame.append(0x00)
            if (value == 38400):
                frame.append(0x80)
                frame.append(0x01)
            if (value == 57600):
                frame.append(0x40)
                frame.append(0x02)
            if (value == 115200):
                frame.append(0x80)
                frame.append(0x04)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame
        if (key == 0x03):
            frame.append(0x07)
            frame.append(0x03)
            if (value == "no"):
                frame.append(0x00)
            if (value == "even"):
                frame.append(0x01)
            if (value == "odd"):
                frame.append(0x02)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame
        if (key == 0x04):
            frame.append(0x07)
            frame.append(0x04)
            if (value == "modbus"):
                frame.append(0x01)
            if (value == "iec101"):
                frame.append(0x02)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame
        print("nothing is read!")
    # param в виде байта управления key в виде конкретного регистра
    def power_management(self,param, key, value):
        frame = [0x55, 0xAA]
        if (param == 0x0C):
            frame.append(0x0C)
            frame.append(0x08)
            frame.append(0x01)
            if (param == 0x00):
                frame.append(0x00)
            if (param == 0x01):
                frame.append(0x01)
            frame.append(0x00)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame

        if (param == 0x04 or param == 0x05 or param == 0x06 or param == 0x07 or param == 0x08 or param == 0x09 or param == 0x87):
            frame.append(param)
            frame.append(0x0A)
            frame.append(key)
            data = float_to_hex(value)
            for d in data:
                frame.append(d)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame
            print("power management is read!")

    def sensor_controls(self,param, key, value):
        frame = [0x55, 0xAA]
        if (param == 0x09 and key == 0x03):
            frame.append(0x09)
            frame.append(0x08)
            frame.append(0x03)
            if (value == "ten"):
                frame.append(0x00)
            if (value == "fan"):
                frame.append(0x01)
            frame.append(0x00)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame

        if (param == 0x09 and key == 0x02):
            frame.append(0x09)
            frame.append(0x08)
            if (key == 0x04 and value == "on"):
                frame.append(0x04)
                frame.append(0x01)
            else:
                frame.append(0x02)
                frame.append(value)
            frame.append(0x00)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame

        if (param == 0x0B):
            frame.append(0x0B)
            frame.append(0x07)
            frame.append(key)
            frame.append(value)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame

        if (param == 0x8A):
            frame.append(0x8A)
            frame.append(0x0E)
            frame.append(key)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            frame.append(0x00)
            crc = self.crc_calculate(frame)
            frame.append(crc)
            return frame

    def serial_number(self,value):
        frame = [0x55, 0xAA, 0x33, 0x09]
        temp = []
        while value > 0:
            byte = value % 0x100
            temp.append(byte)
            value //= 0x100
        while len(temp) < 4:
            temp.append(0x00)
        frame.append(temp[0])
        frame.append(temp[1])
        frame.append(temp[2])
        frame.append(temp[3])
        crc = self.crc_calculate(frame)
        frame.append(crc)
        return frame

    def crc_calculate(self,frame):
        i = 2
        crc = 0x00
        while i < len(frame):
            crc = crc + frame[i]
            i = i + 1
        while crc > 256:
            crc = crc - 256
        return crc

def load_param():
    print("Parameters load")

def float_to_hex(f):
    data = []
    if f == 0:
        data.append(0)
        data.append(0)
        data.append(0)
        data.append(0)
    else:
        temp2 = hex(struct.unpack('<I', struct.pack('<f', f))[0])[2:]
        data.append(int(temp2[6:8],16))
        data.append(int(temp2[4:6],16))
        data.append(int(temp2[2:4],16))
        data.append(int(temp2[0:2],16))
    return data
#   0x17 function modbus
# # 0x01 0x17 0x40 0x55 0x00 0x04 0x40 0xAA 0x00 0x04 [длина фрейма 232] [фрейм 232] [hi] [lo]


# С записью понятно, теперь считывание
if __name__ == '__main__':
    print("Float: ",1)
    my = FloatToHex.floattohex(1)
    print("FloatToHex: ",my)
    my = hex(my)
    print("hex: ", my)
    my = int(my,16)
    print("int: ", my)
    my = FloatToHex.hextofloat(my)
    print("HexToFloat: ", my)
    # 0x3f800000

    f = open('settings.cfg', 'r')
    params = {}
    for line in f:
        temp = line.split(':')
        for t in temp:
            par_name = t.split("=")
            params.update({par_name[0] : par_name[1]})
    #
    # # начало формирования фреймов
    package = []
    write = WriteParam()
    # print("ModSetConsole for PSC 24_10")

    # # Записать серийник
    # print("Enter serial number")
    # serial_number = int(input()[3:])
    # package.append(write.serial_number(serial_number))

    # # сетевые настройки
    # package.append(write.network_settings(registers_pointer.get(0x01).get("InterfaceAdress"),int(params.get("InterfaceAdress"))))
    # package.append(write.network_settings(registers_pointer.get(0x01).get("InterfaceSpeed"), int(params.get("InterfaceSpeed"))))
    # package.append(write.network_settings(registers_pointer.get(0x01).get("InterfaceChet"), params.get("InterfaceChet")))
    # package.append(write.network_settings(registers_pointer.get(0x01).get("ProtocolType"), params.get("ProtocolType")))
    #
    # # управление питанием pw1
    # package.append(write.power_management(register_names.get("pw1u"), registers_pointer.get(0x04).get("pw1_u_nom"), float(params.get("pw1_u_nom"))))
    # package.append(write.power_management(register_names.get("pw1u"), registers_pointer.get(0x04).get("pw1_u_min"), float(params.get("pw1_u_min"))))
    # package.append(write.power_management(register_names.get("pw1u"), registers_pointer.get(0x04).get("pw1_u_max"), float(params.get("pw1_u_max"))))
    # package.append(write.power_management(register_names.get("pw1u"), registers_pointer.get(0x04).get("pw1_u_min_hyst"), float(params.get("pw1_u_min_hyst"))))
    # package.append(write.power_management(register_names.get("pw1u"), registers_pointer.get(0x04).get("pw1_u_max_hyst"), float(params.get("pw1_u_max_hyst"))))
    #
    # # управление питанием pw2
    # package.append(write.power_management(register_names.get("pw2u"), registers_pointer.get(0x05).get("pw2_u_nom"), float(params.get("pw2_u_nom"))))
    # package.append(write.power_management(register_names.get("pw2u"), registers_pointer.get(0x05).get("pw2_u_min"), float(params.get("pw2_u_min"))))
    # package.append(write.power_management(register_names.get("pw2u"), registers_pointer.get(0x05).get("pw2_u_max"), float(params.get("pw2_u_max"))))
    # package.append(write.power_management(register_names.get("pw2u"), registers_pointer.get(0x05).get("pw2_u_min_hyst"), float(params.get("pw2_u_min_hyst"))))
    # package.append(write.power_management(register_names.get("pw2u"), registers_pointer.get(0x05).get("pw2_u_max_hyst"), float(params.get("pw2_u_max_hyst"))))
    #
    # # управление питанием pw3 (BTR)
    # package.append(write.power_management(register_names.get("btru"), registers_pointer.get(0x06).get("btr_u_nom"), float(params.get("btr_u_nom"))))
    # package.append(write.power_management(register_names.get("btru"), registers_pointer.get(0x06).get("btr_u_min"), float(params.get("btr_u_min"))))
    # package.append(write.power_management(register_names.get("btru"), registers_pointer.get(0x06).get("btr_u_max"), float(params.get("btr_u_max"))))
    # package.append(write.power_management(register_names.get("btru"), registers_pointer.get(0x06).get("btr_u_min_hyst"), float(params.get("btr_u_min_hyst"))))
    # package.append(write.power_management(register_names.get("btru"), registers_pointer.get(0x06).get("btr_u_max_hyst"), float(params.get("btr_u_max_hyst"))))
    # #
    # управление питанием outi
    # package.append(write.power_management(register_names.get("outi"), registers_pointer.get(0x07).get("out_i_1"), float(params.get("out_i_1"))))
    # package.append(write.power_management(register_names.get("outi"), registers_pointer.get(0x07).get("out_i_2"), float(params.get("out_i_2"))))
    package.append(write.power_management(0x87, registers_pointer.get(0x07).get("out_i_1"),float(0)))
    # package.append(write.power_management(register_names.get("outi"), registers_pointer.get(0x07).get("out_i_2"),float(0)))
    # #
    # # управление АКБ
    # package.append(write.power_management(register_names.get("charge"), registers_pointer.get(0x08).get("charge_err_min"), float(params.get("charge_err_min"))))
    # package.append(write.power_management(register_names.get("charge"), registers_pointer.get(0x08).get("charge_u_max"), float(params.get("charge_u_max"))))
    # package.append(write.power_management(register_names.get("charge"), registers_pointer.get(0x08).get("charge_u_min"), float(params.get("charge_u_min"))))
    # package.append(write.power_management(register_names.get("charge"), registers_pointer.get(0x08).get("charge_i_stable"), float(params.get("charge_i_stable"))))
    # package.append(write.power_management(register_names.get("charge"), registers_pointer.get(0x08).get("charge_u_stable"), float(params.get("charge_u_stable"))))
    #
    #
    #                                     #!!!!!!!!!!!!!!!!!ДАТЧИКИ!!!!!!!!!!!!!!!!!!!
    # # # установить температуру, через функцию power_management (там реализован FLOAT32)
    # # package.append(write.power_management(0x09, 0x01, -10))
    # # # управление датчиками (режим ten или fan)
    # # package.append(write.sensor_controls(0x09, 0x03, "ten"))
    # # # Включить защиту от холодного старта
    # # package.append(write.sensor_controls(0x09, 0x04, "on"))
    # # # включить все датчики
    # # package.append(write.sensor_controls(0x09, 0x02, 31))
    # # # выключить все датчики
    # # package.append(write.sensor_controls(0x09, 0x02, 0))
    # # # Считать ID с линии 1 в датчик
    # # package.append(write.sensor_controls(0x0B, 0x01, 0xAA))
    # # package.append(write.sensor_controls(0x8A, 0x01, 0))
    # # # # Считать ID с линии 2 в датчик
    # # package.append(write.sensor_controls(0x0B, 0x02, 0xAA))
    # # package.append(write.sensor_controls(0x8A, 0x02, 0))
    # # # # Считать ID с линии 3 в датчик
    # # package.append(write.sensor_controls(0x0B, 0x03, 0xAA))
    # # package.append(write.sensor_controls(0x8A, 0x03, 0))
    # # # # Считать ID с линии 4 в датчик
    # # package.append(write.sensor_controls(0x0B, 0x04, 0xAA))
    # # package.append(write.sensor_controls(0x8A, 0x04, 0))
    # # # # Считать ID с линии 5 в датчик
    # # package.append(write.sensor_controls(0x0B, 0x05, 0xAA))
    # # package.append(write.sensor_controls(0x8A, 0x05, 0))
    #
    #
    # # 0x01 0x17 0x40 0x55 0x00 0x04 0x40 0xAA 0x00 0x04 [длина фрейма 232] [фрейм 232] [непонятная хуйня] [CRC]
    #

    # print("Modbus or Serial? - m or s" )
    # key = input()
    # com = ''
    # braudrate = 115200
    # timeout = 1
    # if key == "m":
    #     com = 'com5'
    #     braudrate = 115200
    #     timeout = 1
    # if key == "s":
    #     com = 'com6'
    #     braudrate = 2400
    #     timeout =1
    ser = serial.Serial('com10', 2400, timeout=0.3)
    for frame in package:
        values = bytearray(frame)
        print("write: ", values)
        ser.write(values)
        response = ser.read(len(values))
        print("read: ", response)
        print(values == response)
        for rep in response:
            print(int(rep))
        # time.sleep(0.5)
    #
    #
    # # frame = create_package("select_pwr", "select_pw", 2)
