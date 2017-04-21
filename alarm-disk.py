#!/usr/bin/env cky-python
import subprocess
# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText





dirs = [["April", "goehring"],
        ["Hongtao","zhho"],
        ["jie","jiey"],
        ["jingpeng","gai"],
        ["johannes","elferich"],
        ["Jonathan","colemajo"],
        ["Juan","duj"],
        ["Nate","yodern"],
        ["sandip","chowdhus"],
        ["Shanshuang","chesh"],
        ["Xianqiang","sonxi"],
        ["Yan","zhaya"],
        ["Zad","jalaliya"]
        ]

for user in dirs:
    res = subprocess.check_output("find %s -type f -mtime +30 -print0 | du -c --files0-from - | tail -n 1" % (user[0]), shell=True)
    size = int(res.split(b'\t')[0])
    if size > 1000000000:
        message = """
Hi,

data of yours that is older than a month is using more than a TB of disk space on eppec (%.2f TB). 
Please consider backing up this data elsewhere and deleting it from eppec.

Thanks,

Johannes
(This is an automated message)
        """ % (size/1000000000)
        msg = MIMEText(message)
        msg['Subject'] = 'Data on eppec - %s' % (user[1])
        msg['From'] = "elferich@ohsu.edu"
        me = msg['From']
        msg['To'] = user[1]+"@ohsu.edu"
        you = msg['To']


        s = smtplib.SMTP('localhost')
        s.sendmail(me, [you], msg.as_string())
        s.quit()
