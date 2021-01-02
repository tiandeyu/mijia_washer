## 米家洗衣机


>mijia_washer是一款ha自定义插件,通过miio协议接入到homeassistant
>可以获取实时状态，控制洗衣机启停(暂不支持)等


### 下载custom component
下载下面网址所有文件到如下目录/config/custom_components/
https://github.com/tiandeyu/mijia_washer/tree/main/custom_components

```shell
//文件目录结构如下
/config/custom_components/mijia_washer/__init__.py
/config/custom_components/mijia_washer/fan.py
/config/custom_components/mijia_washer/manifest.json
```

### configuration.yaml配置 
| 名称 | 可选 | 描述 |
| :---- | :---: | ----- |
| name | 否 | ha的名字(Friendly Name) |
| host | 否 | 洗衣机的IP地址，需要在路由器设为固定IP |
| token | 否 | 米家设备token |
| scan_interval | 是 | 刷新间隔s，默认30 |
 
```yaml
binary_sensor:
  - platform: mijia_washer
    name: 'Washing Machine'
    host: 192.168.2.55
    token: 5fef98a2990ba6068d3fa09c6f892eed
    scan_interval: 10


