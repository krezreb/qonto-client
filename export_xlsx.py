#!/bin/env python3

# -*- coding: utf-8 -*-

from qonto_client import QontoClient, QontoXlsxTransaction
import os, argparse, zipfile, requests
from datetime import datetime, timezone
import shutil
import xlsxwriter


ID=os.getenv("ID")
IBAN=os.getenv("IBAN")
KEY=os.getenv("KEY")

parser = argparse.ArgumentParser(description="Qonto OFX exporting script")
parser.add_argument('--attachments', action='store_true', help='export attachments')
parser.add_argument('--dir', default=None, help='directory to save XLSX file to')
parser.add_argument('--out', default=None, help='path to save XLSX file to')
parser.add_argument('--start-date', default=None, help='fetch transactions on or after UTC date expressed as YYYY-MM-DD')
parser.add_argument('--end-date', default=None, help='fetch transactions on or before UTC  date expressed as YYYY-MM-DD')
parser.add_argument('--last-month', action='store_true', help='fetch transactions from last completed month')

args = parser.parse_args()

Q = QontoClient(
    api_id = ID,
    api_key= KEY,
    iban = IBAN
)

if args.dir == None:
    N = datetime.now()
    args.dir = "{}-{}-{}_{}-{}-{}_{}_qonto".format(N.year, N.month, N.day, N.hour, N.minute, N.second, ID)


if args.dir != None:
    if not os.path.isdir(args.dir):
        os.makedirs(args.dir)

attachment_num = 0

filters = {}

if args.last_month:
    now = datetime.now()
    Y_1 = now.year
    M_1 = now.month-1
    if M_1 == 0:
        M_1 = 12
        Y_1 = now.year - 1

    args.start_date = "{}-{}-01".format(Y_1, M_1)
    args.end_date = "{}-{}-01".format(now.year, now.month)


if args.start_date != None:
    Y, M, D = args.start_date.split("-")
    filters["settled_at_from"] = datetime(int(Y),int(M),int(D), hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

if args.end_date != None:
    Y, M, D = args.end_date.split("-")
    filters["settled_at_to"] = datetime(int(Y),int(M),int(D), hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)







if args.out == None and  args.dir == None :
    print("Please specify either a --dir or --out option")
    exit(-1)
else:
        
    outfn = args.out
    if args.dir != None:

        if args.dir[-1] == "/":
            args.dir = args.dir[:-1]

        if args.out == None:
            outfn = "{}/{}".format(args.dir, os.path.basename(args.dir)+".xlsx")

    else:
        outfn = "{}/{}".format(args.dir, args.out)

    workbook = xlsxwriter.Workbook(outfn, {'default_date_format':
                                                  'yyyy-mm-dd'})
    worksheet = workbook.add_worksheet()

    row = 0
    col = 0

    # writer column headers
    for v in QontoXlsxTransaction.cols().values():
        worksheet.write(row, col, v.capitalize())
        col += 1

    
    for t in Q.transactions(filters=filters):
        col = 0
        row += 1
        QT = QontoXlsxTransaction(t)

        for v in QT.get().values():
            worksheet.write(row, col, v)
            col += 1

        if args.attachments:
            attachment_num = 0
            for url, filename, attachment_id in Q.attachment_urls(t["id"]):
                attachment_num+=1
                with requests.get(url, stream=True) as fh:
                    fh.raise_for_status()
                    fn = "{}-attachment-{}-{}".format(t["transaction_id"], attachment_num, filename)
                    if args.dir != None:
                        fn = "{}/{}".format(args.dir, fn)

                    with open(fn, 'wb') as f:
                        for chunk in fh.iter_content(chunk_size=8192): 
                            # If you have chunk encoded response uncomment if
                            # and set chunk_size parameter to None.
                            #if chunk: 
                            f.write(chunk)
                            
    workbook.close()
