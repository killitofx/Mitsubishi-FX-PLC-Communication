# Mitsubishi-FX-PLC-Communication
这是一个使用PC和PLC通信的项目
## 使用方法
* 初始化  把PLC使用的串口号传入就能完成初始化  
    `fx_plc = FX_PLC_CTR('com5')`
* 读取PLC内部参数  
  `fx_plc.digital_read(Regional,point,read_byte_number=1,_bit=1,raw=0)`  
  * Regional为PLC内部存储区域，暂时支持X，Y，D，M 不支持D区特殊继电器，如D8000以后的）  
  * point 为PLC地址编号  
  * read_byte_number 为一次读取的BYTE数，默认为1，读取8位数据，在Regional为D时失效  
  * _bit 为只输出当前地址的数据，默认为1，0/1可选，当该值为1时且read_byte_number=1，输出当前地址的值，在Regional为d时失效 
  * raw 为输出PLC返回的原始值的开关，默认为0。当为1时，该函数返回PLC输出的原始数据  
* 写入PLC参数  
  `digital_write(Regional,point,data,_bit=1,write_byte_number=1)`  
  * Regional为PLC内部存储区域，暂时支持Y，D，M（不支持D区特殊继电器，如D8000以后的） 
  * point 为PLC地址编号
  * data 为写入值，在对Y区和M区，值为1，0（通/断），在D区为二进制字符串
  * _bit 为只修改当前bit，默认为1，为0时，data中需写入整个byte的数据。该参数对D区无效
  * write_byte_number 当目标区域为Y或M区且_bit=时无效。该参数为一次写入的byte量，推荐不能超过4  
  * 该函数的返回值为1，表示执行成功，为0表示执行失败
## 栗子
  * 读取X0的值
    `fx_plc.digital_read('x',0)`  
    返回值为0，表示当前X0无输入；返回1，表示当前X0有输入  

  * 读取Y0-Y7的值
    `fx_plc.digital_read('y',0,_bit=0)`  
    point为0-7中的任意值即可，返回值为00000010，表示Y7,Y6,Y5,Y4,Y3,Y2,Y1,Y0的状态，由此可知，Y1处于接通状态  

  * 读取Y0-Y17的值
    `fx_plc.digital_read('y',0,2)`   
    返回值为 0000000000000010，对应Y17-Y0的状态  

  * 读取M8-M15的PLC原始返回值
    `fx_plc.digital_read('m',8,raw=1)`  
    返回值为 2 30 30 3 36 33，可对照三菱PLC通信协议自行解读  

  * 读取D123的值 
    `fx_plc.digital_read('d',123)`  
    返回值为0000000000000000，一个D占用16bit的空间
  
  * 修改M128的值为1 
    `fx_plc.digital_write('m',128,1)`  
    返回值为1，表示操作成功  

  * 修改Y7-Y0的值为'00110101'
    `fx_plc.digital_write('y',0,'00110101',0)`  
    返回值为1，表示操作成功 其中point可为Y0-Y7中任意值  

  * 修改D509的值为10 `fx_plc.digital_write('d',509,fx_plc.dec_2_bin(10))`  
    由于data参数需要二进制值，在此使用内部提供的方法`dec_2_bin(10)` 把十进制值10转换成二进制字符串    

  * 修改M0-M15的值 `fx_plc.digital_write('m',0,'1000000000000001',0,2)` 
    返回值1，表示操作成功，查看程序，M0和M15吸合


