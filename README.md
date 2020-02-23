# Mitsubishi-FX-PLC-Communication
这是一个使用PC和PLC通信的项目
## 使用方法
* 初始化  
    > fx_plc = FX_PLC_CTR('com5')

    把PLC使用的串口号传入就能完成初始化
* 读取PLC内部参数
  > fx_plc.digitalRead(Regional,point,read_byte_number=1,_bit=1,raw=0)  

  Regional为PLC内部存储区域，暂时支持X，Y，D，M  
  point 为PLC地址编号  
  read_byte_number 为一次读取的BYTE数，默认为1，读取8位数据，在Regional为D时失效  
  _bit 为只输出当前地址的数据，默认为1，0/1可选，当该值为1时且read_byte_number=1，输出当前地址的值，在Regional为d时失效 
  raw 为输出PLC返回的原始值的开关，默认为0。当为1时，该函数返回PLC输出的原始数据  
    
  * 读取X0的值  
    > fx_plc.digitalRead('x',0)  

    返回值为0，表示当前X0无输入；返回1，表示当前X0有输入  
  * 读取Y0-Y7的值  
    > fx_plc.digitalRead('y',0,_bit=0)  

    point为0-7中的任意值即可，返回值为00000010，表示Y7,Y6,Y5,Y4,Y3,Y2,Y1,Y0的状态，由此可知，Y1处于接通状态  
  * 读取Y0-Y17的值  
    > fx_plc.digitalRead('y',0,2)  

    返回值为 0000000000000010，对应Y17-Y0的状态
  * 读取M8-M15的PLC原始返回值
    > fx_plc.digitalRead('m',8,raw=1)  

    返回值为 2 30 30 3 36 33，可对照三菱PLC通信协议自行解读
  * 读取D123的值 
    > fx_plc.digitalRead('d',123)
    
    返回值为0000000000000000，一个D占用16bit的空间


