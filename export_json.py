#!/bin/env python3

from qonto import QontoClient, QontoOfxTransaction, QontoOfx
import os, argparse

ID=os.getenv("ID")
IBAN=os.getenv("IBAN")
KEY=os.getenv("KEY")

parser = argparse.ArgumentParser(description="OS distro info tool")
parser.add_argument('--attachments', action='store_true', help='display debug messages')
parser.add_argument('--dir', default=None, help='directory to save ofx file to')
parser.add_argument('--out', default=None, help='directory to save ofx file to')
parser.add_argument('--pretty', action='store_true', help='pretty format ofx file')

args = parser.parse_args()

Q = QontoClient(
    api_id = ID,
    api_key= KEY,
    iban = IBAN
)

QO = QontoOfx(iban=IBAN, curdef=Q.currency(), balance=Q.balance(), balancedt=Q.balancedt())

for t in Q.transactions():
    QO.add_transaction(QontoOfxTransaction(t))


ofx = QO.export(pretty=args.pretty)

if args.out == None and  args.dir == None :
    print(ofx)
else:

    outfn = args.out
    if args.dir != None:

        if not os.path.isdir(args.dir):
            os.makedirs(args.dir)

        if args.dir[-1] == "/":
            args.dir = args.dir[:-1]

        if args.out == None:
            outfn = "{}/{}".format(args.dir, os.path.basename(args.dir)+".ofx")

        else:
            outfn = "{}/{}".format(args.dir, args.out)

    with open(outfn, "w") as fh:
        fh.write(ofx)