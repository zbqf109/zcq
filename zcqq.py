#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import os
import sys
import argparse
from pyzcqq import QQReg

parser = argparse.ArgumentParser(description='QQ register configuration.')
parser.add_argument('-r', '--random', type=int,
                   help='set non-zero to randonly generate nicks, passwords, birthdays, areas etc.')
parser.add_argument('-c', '--captcha', type=str,
                   help='where to get captcha, reasonable values are: console, ruokuai')
parser.add_argument('-p', '--phone', type=str,
                   help='where to get phone numbers, reasonable values are: console, remote')
parser.add_argument('-pl', '--phone-list', type=str, dest='phone_list',
        help='if `phone` is set to `local`, place the phone list here, each by comma seperated')
parser.add_argument('-ru', '--ruokuai-user', dest='rk_user', type=str,
                   help='if use `-c ruokuai`, this option specifies ruokuai username')
parser.add_argument('-rp', '--ruokuai-password', dest='rk_pass', type=str,
                   help='if use `-c ruokuai`, this option specifies ruokuai username')
parser.add_argument('-s', '--server', type=str,
                    help='Server ip and port')
                   

# parser.add_argument('--sum', dest='accumulate', action='store_const',
                   # const=sum, default=max,
                   # help='sum the integers (default: find the max)')


args = parser.parse_args()

phone_list = args.phone_list.split(',') if args.phone_list is not None else None

qqreg = QQReg(
            random=args.random, 
            captcha=args.captcha, 
            phone=args.phone, 
            phone_list=phone_list,
            rk_user=args.rk_user, 
            rk_pass=args.rk_pass,
            server=args.server
        )
qqreg.do_reg()

if __name__ == '__main__':
    pass
    
