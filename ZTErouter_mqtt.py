#!/usr/bin/env python
import requests
import re
from datetime import datetime, timezone
from hashlib import sha256
import xml.etree.ElementTree as ET
from collections import namedtuple
import argparse
import paho.mqtt.client as mqtt
import time
import sys
from traceback import print_exc

class ZTEInfo(object):
    def __init__(self, baseURL, username='admin', pwd=''):
        self.baseURL = baseURL
        self.username = username
        self.pwd = pwd
        self.LEDStatus = ''
        self.IPAddress = ''
        self.WorkIFMac = ''
        self.DNS1 = ''
        self.DNS2 = ''
        self.UpTime = ''
        self.TotalUpTime = ''
    
    def query(self):
        result_root = self._query_data()
        return self._query_apply_processed(result_root)
        
    def _query_data(self):
        session = requests.Session()
        ts = round(datetime.now(timezone.utc).timestamp() * 1000)

        token_url = self.baseURL + '/function_module/login_module/login_page/logintoken_lua.lua'
        login_url = self.baseURL
        data_url = self.baseURL + '/getpage.lua?pid=1005&nextpage=InternetReg_lua.lua' 

        session.get(login_url)
        result = session.get(token_url)
        
        if not result:
            raise RuntimeError('Login Failed!')

        session.post(login_url, data = {
                "Username": self.username,
                "Password":sha256((self.pwd + re.findall(r'\d+',result.text)[0]).encode('utf-8')).hexdigest(),
                "action": "login"
        })

        data_page = session.get(data_url)

        result_root = ET.fromstring(data_page.text)

        logout_url = self.baseURL
        log_out_page = session.post(logout_url, data = {
                "IF_LogOff": 1,
                "IF_LanguageSwitch": "",
                "IF_ModeSwitch": ""
        })
        return result_root
    def _query_apply_processed(self, result_root):
        changed = False
        errors = False
        led_info = result_root.find('OBJ_LEDSTATUS_ID')
        if led_info is None or led_info[0] is None:
                print ('LED check failed!')
                errors = True
        else:
            keys = [key.text for key in led_info[0].findall('ParaName')]
            values = [value.text for value in led_info[0].findall('ParaValue')]
            LEDStatus = values[keys.index('LEDStatus')]
            if self.LEDStatus != LEDStatus:
                changed = True
                print("LEDStatus changed")
                self.LEDStatus = LEDStatus

        gw_info = result_root.find('OBJ_DEFGWINFO_ID')
        if gw_info is None or gw_info[0] is None:
                print ('GW check failed!')
                errors = True
        else:
            keys = [key.text for key in gw_info[0].findall('ParaName')]
            values = [value.text for value in gw_info[0].findall('ParaValue')]
            self.UpTime= values[keys.index('UpTime')]
            IPAddress  = values[keys.index('IPAddress')]
            WorkIFMac  = values[keys.index('WorkIFMac')]
            DNS1       = values[keys.index('DNS1')]
            DNS2       = values[keys.index('DNS2')]
            if self.IPAddress != IPAddress:
                print("IPAddress changed")
                changed = True
                self.IPAddress = IPAddress
            if self.WorkIFMac != WorkIFMac:
                print("WorkIFMac changed")
                changed = True
                self.WorkIFMac = WorkIFMac
            if self.DNS1 != DNS1:
                print("DNS1 changed")
                changed = True
                self.DNS1 = DNS1
            if self.DNS2 != DNS2:
                print("DNS2 changed")
                changed = True
                self.DNS2 = DNS2
        
        up_info = result_root.find('OBJ_DEVINFO_ID')
        if up_info is None or up_info[0] is None:
                print ('UPTIME check failed!')
                errors = True
        else:
            keys = [key.text for key in up_info[0].findall('ParaName')]
            values = [value.text for value in up_info[0].findall('ParaValue')]
            self.TotalUpTime = values[keys.index('UpTime')]
        
        return changed, errors
        
def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gateway', required=False, default="http://10.0.0.138", help="Router IP/DNS")
    parser.add_argument('-a', '--gateway-user', required=False, default="admin", help="Router username")
    parser.add_argument('-p', '--gateway-password', required=False, default="", help="Router password")
    parser.add_argument('-m', '--mqtt-broker', required=False, help="MQTT broker ip/dns")
    parser.add_argument('-q', '--mqtt-port', required=False, default=1883, type=int, help="MQTT broker port")
    parser.add_argument('-u', '--mqtt-user', required=False, help="MQTT broker username")
    parser.add_argument('-v', '--mqtt-password', required=False, help="MQTT broker password")
    
    _args = parser.parse_args()

    _useMQTT = _args.mqtt_broker is not None
    if _useMQTT:
        print("Using broker: {}".format(_args.mqtt_broker))
        try:
            print("Connect MQTT...")
            _client = mqtt.Client("Router")
            _client.username_pw_set(_args.mqtt_user, _args.mqtt_password)
            _client.connect(_args.mqtt_broker, _args.mqtt_port)
            print("MQTT Connection successful")
        except:
            print("MQTT-connection went wrong!")
            sys.exit()
    
    router = ZTEInfo(_args.gateway, username=_args.gateway_user, pwd=_args.gateway_password)
    
    while True:
        try:
            changed, errors = router.query()
        except:
            print("Errors occured!")
            print_exc()
            changed = False
        if _useMQTT:
            if changed:
                _client.publish("Router/LEDStatus", router.LEDStatus)
                _client.publish("Router/IPAddress", router.IPAddress)
                _client.publish("Router/WorkIFMac", router.WorkIFMac)
                _client.publish("Router/DNS1", router.DNS1)
                _client.publish("Router/DNS2", router.DNS2)
            _client.publish("Router/UpTime", router.UpTime)
            _client.publish("Router/TotalUpTime", router.TotalUpTime)
        else:
            if changed:
                print("Router/LEDStatus", router.LEDStatus)
                print("Router/IPAddress", router.IPAddress)
                print("Router/WorkIFMac", router.WorkIFMac)
                print("Router/DNS1", router.DNS1)
                print("Router/DNS2", router.DNS2)
            print("Router/UpTime", router.UpTime)
            print("Router/TotalUpTime", router.TotalUpTime)

        time.sleep(60)

if __name__ == '__main__':
    main(sys.argv)