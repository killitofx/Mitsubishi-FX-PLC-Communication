# import serial
# ser = serial.Serial(
# port='com5',
# baudrate=9600,     # baud rate
# bytesize=7,   # number of databits
# parity=PARITY_EVEN,   # enable parity checking
# stopbits=STOPBITS_ONE, # number of stopbits
# timeout=None,      # set a timeout value, None for waiting forever
# )

# ser.send()



import serial
import string
import binascii
from time import sleep


Octal_number=['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
Hexadecimal_word = {'A':'11','B':'12','C':'13','D':'14','E':'15','F':'16'}

class FX_PLC_CTR(object):
    def __init__(self,port):
        self.s=serial.Serial(port,9600,7,'E',1)

    def __del__(self):
        self.s.close()
    
    def logger(self,level,message):
        print('[{}]:{}'.format(level,message))
    
    # 返回编号对应地址，method为8/10进制
    def get_address_area(self,num,method=10):
        num = int(num)
        if method == 8:
            if num > 177 or '8' in str(num) or '9' in str(num):
                raise  Exception("传入数字格式错误")
            # num+=2
            num = int(num/10)
            if num > 8:
                num -= 2
            return Octal_number[num]
        elif method == 10:
            reduce_num = num % 128
            num = int(reduce_num/8)
            return Octal_number[num]
        else:
            raise  Exception("method 只允许8，10")

    def Hexadecimal_2_ascii(self,num):
        num = str(num)
        if len(num) > 1:
            raise  Exception("每次只允许处理一位")
        if num.isdigit():
            ascii_num = str(30 + int(num))
        else:
            if num.upper() in 'ABCDEF':
                ascii_num = str(int(Hexadecimal_word[num.upper()]) + 30)
        return ascii_num

    def ascii_2_Hexadecimal(self,num):
        num = int(num) -30
        if num >= 0 and num <= 9:
            return str(num)
        elif num >= 11 and num <= 16:
            num = list (Hexadecimal_word.keys()) [list (Hexadecimal_word.values()).index (str(num))]
            return num
        else:
            raise  Exception("参数不合法")
                

    def Checksum(self,data_list):
        sum_cache = 0
        for i in data_list:
            sum_cache += int('0x%s' % i,16)
        # print(sum_cache)
        cache = str(hex(eval(str(sum_cache))))[-2:]
        # print(cache)
        a = self.Hexadecimal_2_ascii(cache[-2])
        b = self.Hexadecimal_2_ascii(cache[-1])
        return (a,b)

    def hex_2_dec(self,num):
        num = int("0x%s" % num,16)
        num = bin(num)[2:].zfill(4)
        return num

    def digitalRead(self,Regional,point,read_byte_number=1,_bit=1,raw=0):
        # 构造元件读取请求参数
        cache = ['30']
        # 检测参数是否合法
        if not Regional.upper() in 'XYMD':
            raise  Exception("{}区暂不支持本操作".format(Regional.upper()))
        # 计算不同分区的地址
        if Regional.upper() == 'X':
            # 计算列分布
            col= self.get_address_area(point,8)
            # 生成地址
            address = '008' + str(col)
            self.logger('DEBUG','读取区块地址{}'.format(address))
            for i in address:
                cache.append(self.Hexadecimal_2_ascii(i))
        if Regional.upper() == 'Y':
            col= self.get_address_area(point,8)
            address = '00A' + str(col)
            self.logger('DEBUG','读取区块地址{}'.format(address))
            for i in address:
                cache.append(self.Hexadecimal_2_ascii(i))
        if Regional.upper() == 'M':
            col= self.get_address_area(point)
            row = int((int(point) / 128))
            address = '01'+str(row) + str(col)
            self.logger('DEBUG','读取区块地址{}'.format(address))
            for i in address:
                cache.append(self.Hexadecimal_2_ascii(i))
        if Regional.upper() == 'D':
            _bit=0
            read_byte_number=2
            # 计算列分布
            row= int(point) *2
            col = int(point / 8)
            row = str(hex(row)[-1].upper())
            col = str(hex(col)[-1].upper())
            # 生成地址
            if point < 128:
                address = '10'+ str(col) + row 
            elif point > 127 and point <256:
                address = '11'+ str(col) + row 
            else:
                raise  Exception("不存在该地址")
            self.logger('DEBUG','读取区块地址{}'.format(address))
            for i in address:
                cache.append(self.Hexadecimal_2_ascii(i))
 
    # 构造读取比特开始值
        cache.append('30')
    # 构造读取比特结束值
        cache.append(self.Hexadecimal_2_ascii(read_byte_number))
    # 构造结束符
        cache.append('03')
    # 计算校验码
        a,b = self.Checksum(cache)
        cache.append(a)
        cache.append(b)
    # 构造最终输出指令
        output = '02 '
        for i in cache:
            output += '%s ' % i
        self.logger('DEBUG','准备向PLC发送指令：{}'.format(output))
    # 发送指令
        receive_data = self.send(output)
        
    # 检测是否要返回源码
        cache = ''
        for i in receive_data:
            cache += '%s ' % i
        self.logger('DEBUG','PLC返回指令：{}'.format(cache))
        if raw:
            return cache
    # 解析PLC返回值
    # 判断返回值是否异常
        if 15 in receive_data:
            self.logger('WARNING','PLC表示无法处理该条指令并向你丢出了：{}'.format(receive_data))
            return '请求的指令存在问题'
        # 解析
        else:
            payload = receive_data[1:-3]
            # 在read_byte_number=1且_bit=1时，返回单个地址的值
            if read_byte_number == 1 and _bit:
                a = self.hex_2_dec(self.ascii_2_Hexadecimal(payload[1]))
                b = self.hex_2_dec(self.ascii_2_Hexadecimal(payload[0]))
                p = 8 - (int(point)%8)
                c = (b+a)[p-1:p]
                return int(c)
            # 否则拼接返回值
            else:
                cache = ''
                for i in range(len(payload),0,-2):
                    a = self.hex_2_dec(self.ascii_2_Hexadecimal(payload[i-1]))
                    b = self.hex_2_dec(self.ascii_2_Hexadecimal(payload[i-2]))
                    cache += (b+a)
                return cache




            


    def send(self,data):
        receive= []
        # 发送 
        d=bytes.fromhex(data) 
        self.s.write(d)
        # 接受
        sleep(0.1)
        data_len = self.s.inWaiting()
        for _ in range(data_len):
            data= str(binascii.b2a_hex(self.s.read()))
            receive.append(int(data[2:-1]))
        return receive
    



fx_plc = FX_PLC_CTR('com5')
print(fx_plc.digitalRead('d',123))



