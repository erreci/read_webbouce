import os
import email
import sys
import getopt
import argparse
#import json
import re
import zipfile
import logging

from datetime import datetime
#from datetime import date, timedelta
#from time import sleep, time

# from database import Database
import mysql.connector as db

'''
Creating logger
'''
mylogs = logging.getLogger(__name__)
mylogs.setLevel(logging.DEBUG)

today = datetime.now()
YYYY = today.strftime("%Y")
MM = today.strftime("%m")
NOW = today.strftime("%Y%m%d")
# BASE_LOG = "/data/logs/read_webbounce/"

if sys.platform == 'darwin':
    BASE_LOG = "/Users/macmini/data/webbounce_emails"
elif sys.platform == 'linux':
    BASE_LOG = "/data/log/webbounce_emails"
else:
    BASE_LOG = "C:/Users/LTAPPS01/temp/webbounce_emails"

LOG_NAME = BASE_LOG + "/" + YYYY + "/" + MM + "/" + NOW + '_mail_statistic.log'
USE_DB = 0

# on file
onfile = logging.FileHandler(LOG_NAME)
fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
onfile.setLevel(logging.DEBUG)
onfile.setFormatter(fileformat)

# on console
onstream = logging.StreamHandler()
streamformat = logging.Formatter("%(levelname)s:%(message)s")
onstream.setLevel(logging.DEBUG)
onstream.setFormatter(streamformat)
# Adding all handlers to the logs
mylogs.addHandler(onfile)
mylogs.addHandler(onstream)

first_db = False
second_db = False
second_db_cur = False
first_db_cur = False

try:
    os.makedirs(BASE_LOG + "/" + YYYY + "/" + MM)
except FileExistsError:
    # directory already exists
    pass

def validate_date(mydate):
    format_string = '%Y-%m-%d'
    try:
        datetime.datetime.strptime(mydate, format_string)
        return True
    except ValueError:
        return False

def main(argv):
    global USE_DB
    global first_db
    global second_db
    global second_db_cur
    global first_db_cur
    
    first_db = db.connect(user='usamaildb8', password='8bdliamasu', database='mail', host='usamaildb8.ceiimqxfndkz.us-east-1.rds.amazonaws.com', port=3306)
    if first_db:
            print("db ok")
            first_db.autocommit = False
            first_db_cur = first_db.cursor(buffered=True)
            USE_DB = 1
    else:
        print('failed to connect db')
        exit(1)
    if argv.date:
        if not validate_date(argv.date):
            print ('the date should be yyyy-mm-dd')
            sys.exit()
    at_from = argv.date + " 00:00:00"
    at_to = argv.date + " 23:59:59"
    first_db_cur.execute("select count(*) from mail_receipt mr where added_time >= %s and added_time <= %s;", (at_from,at_to,))
    result = first_db_cur.fetchone()
    if result:
        print(result)
    
    first_db_cur.close()
    first_db.close()



if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--date", type=str, help="YYYY-MM-DD date to set statistics" required=True)
        parser.add_argument("-s", "--show", type=int, help="1 show statistic")
        parser.add_argument('-v', '--version', action='version', version='%(prog)s {} by ErreCi (2022)'.format(__version__))
        args = parser.parse_args()
        main(args)

    except KeyboardInterrupt:
        mylogs.error("Process interrupted by KeyboardInterrupt")


