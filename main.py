import serial
import string
import binascii
from time import sleep,strftime,localtime


Octal_number=['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
Hexadecimal_word = {'A':'11','B':'12','C':'13','D':'14','E':'15','F':'16'}

class FX_PLC_CTR(object):
    def __init__(self,com,show_log_level='INFO'):
        self.s=serial.Serial(com,9600,7,'E',1)
        self.show_log_level = show_log_level

    def __del__(self):
        self.s.close()
    
    def logger(self,level,message):
        level_list = ['DEBUG','INFO','WARING','ERROR']
        # 读取输出等级
        if self.show_log_level in level_list:
            index = level_list.index(self.show_log_level)
        else:
            index = 0
        # 计算输出等级
        if level in level_list:
            _idx = level_list.index(level)
        else:
            _idx = 4
        # 判断是否输出
        if index <= _idx:
            now = strftime("%Y-%m-%d %H:%M:%S", localtime())
            print('{} [{}] {}'.format(now,level,message))
    
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

    def hex_2_bin(self,num):
        num = int("0x%s" % num,16)
        num = bin(num)[2:].zfill(4)
        return num

    def digital_read(self,Regional,point,read_byte_number=1,_bit=1,raw=0):
        self.logger('INFO','准备对PLC进行读操作')
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
        elif Regional.upper() == 'Y':
            col= self.get_address_area(point,8)
            address = '00A' + str(col)
            self.logger('DEBUG','读取区块地址{}'.format(address))
            for i in address:
                cache.append(self.Hexadecimal_2_ascii(i))
        elif Regional.upper() == 'M':
            col= self.get_address_area(point)
            row = int((int(point) / 128))
            address = '01'+str(row) + str(col)
            self.logger('DEBUG','读取区块地址{}'.format(address))
            for i in address:
                cache.append(self.Hexadecimal_2_ascii(i))
        elif Regional.upper() == 'D':
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
            elif point > 255 and point <384:
                address = '12'+ str(col) + row 
            elif point > 383 and point <512:
                address = '12'+ str(col) + row 
            else:
                raise  Exception("不存在该地址")
            self.logger('DEBUG','读取区块地址{}'.format(address))
            for i in address:
                cache.append(self.Hexadecimal_2_ascii(i))
        else:
            raise  Exception("不存在该区域")
 
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
            self.logger('INFO','读操作执行成功')
            payload = receive_data[1:-3]
            # 在read_byte_number=1且_bit=1时，返回单个地址的值
            if read_byte_number == 1 and _bit:
                a = self.hex_2_bin(self.ascii_2_Hexadecimal(payload[1]))
                b = self.hex_2_bin(self.ascii_2_Hexadecimal(payload[0]))
                p = 8 - (int(point)%8)
                c = (b+a)[p-1:p]
                return int(c)
            # 否则拼接返回值
            else:
                cache = ''
                for i in range(len(payload),0,-2):
                    a = self.hex_2_bin(self.ascii_2_Hexadecimal(payload[i-1]))
                    b = self.hex_2_bin(self.ascii_2_Hexadecimal(payload[i-2]))
                    cache += (b+a)
                return cache


    def digital_write(self,Regional,point,data,_bit=1,write_byte_number=1):
        self.logger('INFO','准备对PLC进行写操作')
        cache = ['31']
        # 检测参数是否合法
        if not Regional.upper() in 'YMD':
            raise  Exception("{}区暂不支持本操作".format(Regional.upper()))
        if _bit == 1 and Regional.upper() in 'YM':
            write_byte_number=1
        # 计算不同分区的地址
        if Regional.upper() == 'Y':
            # 获取要修改的元件地址
            col= self.get_address_area(point,8)
            address = '00A' + str(col)
            self.logger('DEBUG','准备修改的区块地址{}'.format(address))
            for i in address:
                cache.append(self.Hexadecimal_2_ascii(i))
            # 修改指定byte
            cache.append('30')
            cache.append(self.Hexadecimal_2_ascii(write_byte_number))
            # 只修改单个bit
            if _bit == 1:
                # 获取位数
                _point = point % 10
                # 检查点数是否合法
                if _point == 8 or _point == 9:
                    raise  Exception("请检测是否存在该地址")
                # 获取原始值
                original_data = self.digital_read('Y',point,_bit=0)
                self.logger('DEBUG','PLC原始数据为{}'.format(original_data))
                # 计算生成数据
                data = original_data[0:7-_point] + str(data) + original_data[8-_point:]
                self.logger('DEBUG','计算出的结果为{}'.format(data))
            # 修改整个byte
            else:
                data = str(data).zfill(8*int(write_byte_number))
                self.logger('DEBUG','准备修改结果为{}'.format(data))


        elif Regional.upper() == 'M':
            col= self.get_address_area(point)
            row = int((int(point) / 128))
            address = '01'+str(row) + str(col)
            self.logger('DEBUG','准备修改的区块地址{}'.format(address))
            for i in address:
                cache.append(self.Hexadecimal_2_ascii(i))
            # 修改指定个byte
            cache.append('30')
            cache.append(self.Hexadecimal_2_ascii(write_byte_number))
            if _bit == 1:
                # 获取位数
                _point = point % 8
                # 获取原始值
                original_data = self.digital_read('M',point,_bit=0)
                self.logger('DEBUG','PLC原始数据为{}'.format(original_data))
                # 计算生成数据
                data = original_data[0:7-_point] + str(data) + original_data[8-_point:]
                self.logger('DEBUG','计算出的结果为{}'.format(data))
            # 修改整个byte
            else:
                data = str(data).zfill(8*int(write_byte_number))
                self.logger('DEBUG','准备修改结果为{}'.format(data))


        elif Regional.upper() == 'D':
            if write_byte_number < 2:
                write_byte_number = 2
            if not write_byte_number % 2 == 0:
                write_byte_number += 1

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
            elif point > 255 and point <384:
                address = '12'+ str(col) + row 
            elif point > 383 and point <512:
                address = '12'+ str(col) + row 
            else:
                raise  Exception("不存在该地址")
            self.logger('DEBUG','准备修改的区块地址{}'.format(address))
            for i in address:
                cache.append(self.Hexadecimal_2_ascii(i))
            # 修改指定个byte
            cache.append('30')
            cache.append(self.Hexadecimal_2_ascii(write_byte_number))
            data = str(data).zfill(8*int(write_byte_number))
            self.logger('DEBUG','准备修改结果为{}'.format(data))
        else:
            raise  Exception("未找到该种区域")



        for i in range(len(data),0,-8):
            high = self.Hexadecimal_2_ascii(hex(int(data[i-8:i-4],2))[-1])
            low = self.Hexadecimal_2_ascii(hex(int(data[i-4:i],2))[-1])
            # 写入数据
            cache.append(high)
            cache.append(low)
        # 结束字符
        cache.append('03')
        # 校验码
        a,b = self.Checksum(cache)
        cache.append(a)
        cache.append(b)
        # 构造最终输出指令
        output = '02 '
        for i in cache:
            output += '%s ' % i
        self.logger('DEBUG','准备向PLC发送指令：{}'.format(output))
        receive_data = self.send(output)

        if receive_data[0] == 6:
            self.logger('INFO','写操作执行成功')
            return 1
        else:
            self.logger('WARNING','写操作执行失败')
            return 0 


    def switch(self,Regional,point,state):
        self.logger('INFO','准备对PLC进行强制ON/OFF操作')
        point = int(point)
        # 检查区域
        if not Regional.upper() in 'SMXYT':
            raise  Exception("{}区暂不支持本操作".format(Regional.upper()))
        # 检查状态
        if state:
            cache = ['37']
        else:
            cache = ['38']
        # 寻找地址
        if  Regional.upper() == 'Y':
            if point > 177 or point < 0:
                raise  Exception("不存在此点位")
            address = self.onoff_address('0500',point,8)
        elif Regional.upper() == 'X':
            if point > 177 or point < 0:
                raise  Exception("不存在此点位")
            address = self.onoff_address('0400',point,8)
        elif Regional.upper() == 'S':
            if point > 999 or point < 0:
                raise  Exception("不存在此点位")
            address = self.onoff_address('0000',point)
        elif Regional.upper() == 'T':
            if point > 255 or point < 0:
                raise  Exception("不存在此点位")
            address = self.onoff_address('0600',point)
        elif Regional.upper() == 'M':
            if point > 1023 or point < 0:
                raise  Exception("不存在此点位")
            address = self.onoff_address('0800',point)
        elif Regional.upper() == 'C':
            if point > 255 or point < 0:
                raise  Exception("不存在此点位")
            address = self.onoff_address('0E00',point)
        elif Regional.upper() == 'SM':
            point -= 8000 
            if point > 255 or point < 0:
                raise  Exception("不存在此点位")
            address = self.onoff_address('0F00',point)
        else:
            raise  Exception("不存在此区域")

        

        # 第一位
        cache.append(self.Hexadecimal_2_ascii(address[2]))
        # 第二位
        cache.append(self.Hexadecimal_2_ascii(address[3]))
        # 第三位
        cache.append(self.Hexadecimal_2_ascii(address[0]))
        # 第四位
        cache.append(self.Hexadecimal_2_ascii(address[1]))
        # 结束符
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
        if receive_data[0] == 6:
            self.logger('INFO','强制ON/OFF操作完成')
            return 1
        else:
            self.logger('WARNING','强制ON/OFF操作失败')
            return 0 



    def onoff_address(self,base_address,point,method=10):
        point = int(point)
        b0 = base_address[0]
        b1 = base_address[1]
        b2 = 0
        b3 = 0
        if method == 10:
            b1 = self.hex_2_dec((base_address[1]))
            # b1 = self.hex_2_dec(int(base_address[1]))
            # 处理第二位
            c1 = int(point/256)
            if c1 > 0:
                b1 = b1 + c1
            b1 = self.dec_2_hex(b1)
            # 处理第三位
            c2 = int(point/16)
            if c2 > 0:
                b2+=c2
            b2 = self.dec_2_hex(b2)
            # 处理第四位
            c3 = int(point%16)
            if c3 > 0:
                b3+=c3
            b3 = self.dec_2_hex(b3)
            output = b0 + str(b1) + str(b2) + str(b3)
            self.logger('DEBUG','准备修改地址：{}'.format(output))
            return output
        if method == 8:
            # 错误处理
            if point > 77 and point < 100:
                raise  Exception("不存在此点位")
            # 处理第三位
            c2 = int(point/20)
            if c2 > 0:
                b2+=c2
            #  八进制修改
            if b2 > 3:
                b2 -=1
            b2 = self.dec_2_hex(b2)
            # 处理第四位
            c3 = int(point%20)
            # 错误处理
            if c3 == 8 or c3 == 9 or c3 == 18 or c3 == 19:
                raise  Exception("不存在此点位")
            # 计算真实值
            if c3>8:
                c3-=2
            b3 = self.dec_2_hex(c3)
            output = b0 + b1 + str(b2) + str(b3)
            self.logger('DEBUG','准备修改地址：{}'.format(output))
            return output

    
    def dec_2_hex(self,num):
        return hex(num)[-1].upper()

    def hex_2_dec(self,num):
        return int('0x{}'.format(num),16)

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
    

    def dec_2_bin(self,num):
        payload = str(bin(int(num))[2:])
        num_len = len(payload)
        if not num_len % 8 == 0:
            num_len += 8 - (num_len % 8)
            payload = payload.zfill(num_len)
        return payload
    


if __name__ == '__main__':
    fx_plc = FX_PLC_CTR('com5')
    fx_plc.switch('y',0,1)
    fx_plc.digital_write('d',123,fx_plc.dec_2_bin(10))
    print(fx_plc.digital_read('d',123))
    



