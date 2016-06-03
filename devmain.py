#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import os
import sys
import time
import json
import base64
import hashlib
import logging
import subprocess
import configparser
import urllib.parse
import urllib.request
import http.cookiejar
import rsa

FORMAT = '[%(asctime)-15s] %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

class LoginFailException(Exception): pass
class NoPhoneException(Exception): pass
class UnImplementationError(Exception): pass

class ClientConfig(object):
    '''Client configuration
    '''
    def __init__(self, configfile):
        self.config = configparser.ConfigParser()
        self.config.read(configfile)


    @property
    def region(self):
        return self.config['Registration']['region']


    @property
    def random(self):
        return self.config['Registration']['random']

    @property
    def phone(self):
        return self.config['Registration']['phone']


    @property
    def interval(self):
        return int(self.config['Registration']['interval'])


    @property
    def pubkey(self):
        return self.config['Registration']['pubkey']


    @property
    def ruokuai(self):
        return self.config['ruokuai']['enable']

    
    @property
    def rk_user(self):
        return self.config['ruokuai']['rk_user']


    @property
    def rk_pass(self):
        return self.config['ruokuai']['rk_pass']


    @property
    def server(self):
        return '{}:{}'.format(self.config['server']['host'], 
                self.config['server']['port'])

    @property
    def sv_user(self):
        return self.config['server']['user']


    @property
    def sv_pass(self):
        return self.config['server']['pass']



clients = []

def find_regdev_by_session(session):
    for c in clients:
        if c.session == session:
            return c
    return 


#class ClientType(type):
#    def __new__(cls, name, bases, attrs):
#        return super(ClientType, cls).__new__(cls, name, bases, attrs)


class RegClient(object):
    '''Registeration client
    '''
    
    def __init__(self, configfile):
        self.config     = ClientConfig(configfile)
        self.server     = self.config.server
        self.name       = self.config.sv_user
        self.password   = self.config.sv_pass
        self.cookies    = http.cookiejar.CookieJar()
        self.session    = ''
        
        self._login_count = 0
        self._login_auth  = ''
        self._phone_cache = 'avaiphones.txt'

        self.reg_process  = []

        clients.append(self)
        
    def login(self):
        self._login_count += 1
        url = 'http://{}/1/{}/4?p={}'.format(self.server, self.name, 
                urllib.parse.quote(self._login_auth))
        logging.info('request pass: %s', self._login_auth)
        
        if self._login_count > 2:
            self._login_count = 0
            raise LoginFailException('Login has been tried too many times')
        
        cookieprocessor = urllib.request.HTTPCookieProcessor(self.cookies)
        self.opener = urllib.request.build_opener(cookieprocessor)
        req = urllib.request.Request(url)
        res = self.opener.open(req)
        
        con = res.read()
        con = con.decode()
        logging.info('response: %s', con)
        if con == 'ok':
            # login success
            logging.info('login success')
            self.cookies.extract_cookies(res, req)
            for ck in self.cookies:
                logging.info('cookie: %s=%s', ck.name, ck.value)
                if ck.name == 's':
                    self.session = ck.value
                    break
            logging.info('session: %s', self.session)
        elif con == 'need authorization':
            # auth
            logging.info('Cookie: %s', res.getheader('Set-Cookie'))
            self.cookies.extract_cookies(res, req)
            n = None
            for ck in self.cookies:
                logging.info('cookie: %s=%s', ck.name, ck.value)
                if ck.name == 'n':
                    n = ck.value
                    break
            b = '{}-{}'.format(n, self.password).encode()
            m = hashlib.md5(b)
            self._login_auth = base64.b64encode(m.digest()).decode()
            return self.login()
        elif con == 'authorized failure':
            # fail
            return False
            
        return True
        
    
    def get_session(self):
        return self.session
        
     
    def get_phones(self):
        url = 'http://{}/1/{}/5'.format(self.server, self.name)
        
        res = self.opener.open(url)
        con = res.read()
        logging.info('con=%s', con)
        if con != b'[]':
            with open(self._phone_cache, 'wb') as f:
                f.write(con)
        con = con.decode()
        logging.info('response: %s', con)
        self.available_phones = json.loads(con)
        logging.info('phones: %s',  self.available_phones)
        return True


    def get_smsvc(self, phone, when):
        url = 'http://{}/1/{}/7?p={}&w={}'.format(self.server, self.name, phone, when)
        cookieprocessor = urllib.request.HTTPCookieProcessor(self.cookies)
        self.opener = urllib.request.build_opener(cookieprocessor)

        while True:
            req = urllib.request.Request(url)
            res = self.opener.open(req)

            con = res.read()
            con = con.decode()
            logging.info('get sms verify code: %s', con)
            if con != 'timeout':
                break
        return con


    def report_phone_sms_limited(self, phone):
        url = 'http://{}/1{}/8?p={}&t=2'.format(self.server, self.name, phone)
        try:
            req = urllib.request.Request(url)
            res = self.opener.open(req)
        except Exception as err:
            pass


    def report_phone_invalid(self, phone):
        url = 'http://{}/1{}/8?p={}&t=3'.format(self.server, self.name, phone)
        try:
            req = urllib.request.Request(url)
            res = self.opener.open(req)
        except Exception as err:
            pass


    def report_uin(self, uin, password, *args, **kwargs):
        url = 'http://{}/1/{}/8'.format(self.server, self.name)
        # uin         = bottle.request.forms.get('uin')
        # ursapass    = bottle.request.forms.get('password')
        # unick       = bottle.request.forms.get('nick')
        # ucountry    = bottle.request.forms.get('country')
        # uprovince   = bottle.request.forms.get('province')
        # ucity       = bottle.request.forms.get('city')
        # ubirth      = bottle.request.forms.get('birth')
        # ugender     = bottle.request.forms.get('gender')
        # uphone      = bottle.request.forms.get('phone')
        # unongli     = bottle.request.forms.get('nongli')
        # uregion     = bottle.request.forms.get('region')
        
        # rsa public key
        with open(self.config.pubkey) as f:
            con = f.read()
        pub_key = rsa.PublicKey.load_pkcs1(con)
        rsapass = rsa.encrypt(password.encode(), pub_key)
        b64pass = base64.b64encode(rsapass).decode()

        params  = {
                'uin'     : uin,
                'password': urllib.parse.quote(b64pass),
                'nick'    : kwargs.get('nick', ''),
                'country' : kwargs.get('country', 1),
                'province': kwargs.get('province', 11),
                'city'    : kwargs.get('city', 1),
                'birth'   : kwargs.get('birth', '1991-1-1'),
                'gender'  : kwargs.get('gender', 1),
                'phone'   : kwargs.get('phone', ''),
                'nongli'  : kwargs.get('nongli', 0),
                'region'  : kwargs.get('region', self.config.region)
        }

        query   = 'uin={uin}&password={password}&nick={nick}&country={country}&province={province}&city={city}&birth={birth}&gender={gender}&phone={phone}&nongli={nongli}&region={region}'.format(**params)
        logging.info('url: %s', url)
        logging.info('query: %s', query)
        try:
            req = urllib.request.Request(url, query.encode())
            res = self.opener.open(req)
        except Exception as err:
            logging.error(err)


    
    def start_reg(self):

        # read from cache
        with open(self._phone_cache, 'rb') as f:
            con = f.read()
            self.available_phones.extend(json.loads(con.decode()))

        if len(self.available_phones) == 0:
            raise  NoPhoneException('no avaiable phone numbers')
            
        if sys.platform == 'win32':
            py = 'py -3'
        else:
            py = 'python3'
            
        for pn in self.available_phones:
            args = [py, 'zcqq.py', 
                    '-r', self.config.random, 
                    '-c', 'ruokuai',
                    '-m', self.name,
                    '-s', self.session]

            #if self.config.phone == 'local':
            #    phones = [p['number'] for p in self.available_phones]
            #    args.extend(['-p', 'local', '-pl', ','.join(phones)])
            #elif self.config.phone == 'remote':
            #    # TODO design remote interface
            #    raise UnImplementationError("phone from remote not implemented.")
            args.extend(['-p', pn])

            if self.config.ruokuai:
                args.extend(['-ru', self.config.rk_user, '-rp', self.config.rk_pass])
            
            sb = subprocess.Popen(args)
            self.reg_process.append(sb)
            
            # sleep for some time
            time.sleep(self.config.interval)

        for sb in self.reg_process:
            sb.wait()
        
        
    def __repr__(self):
        return 'RegClient(name={})'.format(self.name)
    

if __name__ == '__main__':
    rc = RegClient('client.ini')
    try:
        ok = rc.login()
    except Exception as e:
        logging.error(e)
        sys.exit(0)
    else:
        logging.info('login ok')
        rc.get_phones()
    #rc.start_reg()
    #rc.get_smsvc('18157762774', '20160530-161000')
    rc.report_uin('2587277158', '28v39vaFY999', nick='28v39vaFY', phone='18157762594')
        

