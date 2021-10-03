#!/bin/env python3

from qonto import QontoClient, QontoOfx, QontoOfxTransaction
import os, argparse, requests
from datetime import datetime, timezone

ID=os.getenv("ID")
IBAN=os.getenv("IBAN")
KEY=os.getenv("KEY")

parser = argparse.ArgumentParser(description="OS distro info tool")
parser.add_argument('--attachments', action='store_true', help='display debug messages')
parser.add_argument('--dir', default=None, help='directory to save ofx file to')
parser.add_argument('--out', default=None, help='directory to save ofx file to')
parser.add_argument('--pretty', action='store_true', help='pretty format ofx file')
parser.add_argument('--start-date', default=None, help='fetch transactions on or after UTC date expressed as YYYY-MM-DD')
parser.add_argument('--end-date', default=None, help='fetch transactions on or before UTC  date expressed as YYYY-MM-DD')

args = parser.parse_args()

Q = QontoClient(
    api_id = ID,
    api_key= KEY,
    iban = IBAN
)

QO = QontoOfx(iban=IBAN, curdef=Q.currency(), balance=Q.balance(), balancedt=Q.balancedt())

if args.dir != None:
    if not os.path.isdir(args.dir):
        os.makedirs(args.dir)

attachment_num = 0

filters = {}
if args.start_date != None:
    Y, M, D = args.start_date.split("-")
    filters["settled_at_from"] = datetime(int(Y),int(M),int(D), hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

if args.end_date != None:
    Y, M, D = args.end_date.split("-")
    filters["settled_at_to"] = datetime(int(Y),int(M),int(D), hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

for t in Q.transactions(filters=filters):
    QO.add_transaction(QontoOfxTransaction(t))
    if args.attachments:
        for url, filename, attachment_id in Q.attachment_urls(t["id"]):
            attachment_num+=1
            with requests.get(url, stream=True) as fh:
                fh.raise_for_status()
                fn = "attachment-{}-id-{}-{}".format(attachment_num, attachment_id[0:8], filename)
                if args.dir != None:
                    fn = "{}/{}".format(args.dir, fn)

                with open(fn, 'wb') as f:
                    for chunk in fh.iter_content(chunk_size=8192): 
                        # If you have chunk encoded response uncomment if
                        # and set chunk_size parameter to None.
                        #if chunk: 
                        f.write(chunk)


ofx = QO.export(pretty=args.pretty)

if args.out == None and  args.dir == None :
    print(ofx)
else:

    outfn = args.out
    if args.dir != None:

        if args.dir[-1] == "/":
            args.dir = args.dir[:-1]

        if args.out == None:
            outfn = "{}/{}".format(args.dir, os.path.basename(args.dir)+".ofx")

        else:
            outfn = "{}/{}".format(args.dir, args.out)

    with open(outfn, "w") as fh:
        fh.write(ofx)

    