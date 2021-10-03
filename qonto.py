#!/bin/env python3

import requests
from datetime import datetime, timezone, tzinfo, timedelta

from ofxtools.models import *
from ofxtools.utils import UTC
from ofxtools.header import make_header
import xml.etree.ElementTree as ET

from decimal import Decimal
from schwifty import IBAN
from dateutil import tz
import lxml.etree as etree

class QontoClient():

    API_ROOT = "https://thirdparty.qonto.com"

    def __init__(self, api_id, api_key, iban) -> None:
        
        self.api_id = api_id
        self.api_key = api_key
        self.iban = iban
        self.account = None

    def auth(self):
        return {'Authorization': "{}:{}".format(self.api_id, self.api_key)}

    # SEE https://api-doc.qonto.com/docs/business-api/b3A6ODQxOTQyNw-list-transactions
    def transactions(self, page=1, filters={}):
        url = '{}/v2/transactions?iban={}'.format(self.API_ROOT, self.iban)
        for k,v in filters.items():
            if type(v) is list:
                for vv in v:
                    url+= "&{}[]={}".format(k,vv)
            if type(v) is datetime:
                url+= "&{}={}".format(k,v.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%m:%S.000Z"))
            else:
                url+= "&{}={}".format(k,v)
        if page > 1:
            url+= "&page={}".format(page)
        headers = self.auth()
        r = requests.get(url, headers=headers)
        print(url)
        for t in r.json()['transactions']:
            yield t

        if r.json()['meta']['current_page'] < r.json()['meta']['total_pages']:
            yield from self.transactions(page=page+1, filters=filters)

    # SEE https://api-doc.qonto.com/docs/business-api/b3A6ODQxOTQyNw-list-transactions
    def show_transaction(self, transaction_id):
        url = '{}/v2/transactions/{}'.format(self.API_ROOT, transaction_id)
        r = requests.get(url, headers=self.auth())
        return r.json()['transaction']

    def get_account(self) -> None:
        if self.account == None:
            url = '{}/v2/organizations/{}'.format(self.API_ROOT, self.api_id)

            r = requests.get(url, headers=self.auth())
            for t in r.json()['organization']["bank_accounts"]:
                if t['iban'] == self.iban:
                    self.account = t
                    return 

    def balance(self,):
        self.get_account()
        return self.account["balance"]

    def balancedt(self,):
        self.get_account()
        return datetime.strptime(self.account["updated_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()) 

    def currency(self,):
        self.get_account()
        return self.account["currency"]

    def attachment_urls(self, transaction_id):
        url = '{}/v2/transactions/{}/attachments'.format(self.API_ROOT, transaction_id)
        r = requests.get(url, headers=self.auth())
        for att in r.json()["attachments"]:
            yield att["url"], att["file_name"], att['id']

class QontoOfxTransaction():
    def __init__(self, j={}):

        if j["operation_type"] == "qonto_fee":
            self.TRNTYPE = "FEE"

        if j["operation_type"] == "direct_debit":
            self.TRNTYPE = "DIRECTDEBIT"

        if j["operation_type"] == "card":
            self.TRNTYPE = "DEBIT"

        if j["operation_type"] == "transfer":
            self.TRNTYPE = "XFER"

        if j["operation_type"] == "income":
            self.TRNTYPE = "CREDIT"

        self.DTPOSTED = datetime.strptime(j["settled_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=tz.tzutc()) # 2020-02-25T08:01:48.727Z
        self.TRNAMT = j["local_amount"]
        if j["side"] == "debit":
            self.TRNAMT = -self.TRNAMT
        self.FITID = j["transaction_id"]
        self.NAME = j["label"]
        self.MEMO = j["note"]

        if j["reference"] != None:
            self.MEMO = j["reference"]


    def get(self):
        if self.MEMO == None:
            return STMTTRN(trntype=self.TRNTYPE, dtposted=self.DTPOSTED, trnamt="{:.2f}".format(self.TRNAMT), fitid=self.FITID, name=self.NAME)
        return STMTTRN(trntype=self.TRNTYPE, dtposted=self.DTPOSTED, trnamt="{:.2f}".format(self.TRNAMT), fitid=self.FITID, name=self.NAME, memo=self.MEMO)


class InvalidIban(Exception):
    pass

def parse_iban(iban):
    i = IBAN(iban)

    if not i.is_valid:
        raise(InvalidIban("{} is not a valid IBAN".format(iban)))

    I = {}
    for k in ('account_code', 'bank_code', 'bban', 'bic', 'branch_code', 'checksum_digits', 'compact', 'country', 'country_code'):
        I[k] = getattr(i, k)

    return I

class QontoOfx():

    def __init__(self, sonrs_language='ENG', curdef='EUR', iban=None, balance=None, balancedt:datetime=datetime.utcnow(),
        accttype='CHECKING') -> None:
        
        self.sonrs_language = sonrs_language
        self.curdef = curdef
        self.iban = parse_iban(iban)
        self.accttype = accttype
        self.balance = balance
        self.balancedt = balancedt

        self.transactions = []
        self.transactions_dtstart = None
        self.transactions_dtend = None
        self.transactions_dtend = None


    def acctfrom(self):
        return BANKACCTFROM(
            bankid=self.iban["bank_code"], 
            acctid=self.iban["account_code"][5:16],
            accttype=self.accttype,
            acctkey=self.iban["account_code"][-2:],
            branchid=self.iban["account_code"][0:5]) 

    def ledgerbal(self):
        return  LEDGERBAL(balamt="{:.2f}".format(self.balance),  dtasof=self.balancedt)

    def banktranlist(self):
        return BANKTRANLIST(*self.transactions, dtstart=self.transactions_dtstart, dtend=self.transactions_dtend)


    def stmttrnrs(self, trnuid='XXXXX', status_code=0, status_severity='INFO'):
        return STMTTRNRS(trnuid=trnuid, status=self.status(status_code, status_severity), stmtrs=self.stmtrs())

    def stmtrs(self,):
        return STMTRS(curdef=self.curdef, bankacctfrom=self.acctfrom(),
            ledgerbal=self.ledgerbal(),
            banktranlist=self.banktranlist())
            
    def status(self, code=0, severity='INFO'):
        return  STATUS(code=code, severity=severity)

    def fi(self):
        return FI(org='QONTO')

    def add_transaction(self, tr: QontoOfxTransaction):

        if self.transactions_dtstart == None:
            self.transactions_dtstart = tr.DTPOSTED
        elif tr.DTPOSTED < self.transactions_dtstart:
            self.transactions_dtstart = tr.DTPOSTED

        if self.transactions_dtend == None:
            self.transactions_dtend = tr.DTPOSTED
        elif tr.DTPOSTED > self.transactions_dtend:
            self.transactions_dtend = tr.DTPOSTED

        self.transactions.append(tr.get())


    def export(self, pretty=False):

        sonrs = SONRS(status=self.status(),dtserver=datetime.now(timezone.utc),  language=self.sonrs_language, fi=self.fi())
        signonmsgsrsv1 = SIGNONMSGSRSV1(sonrs=sonrs)

        bankmsgsrsv1 = BANKMSGSRSV1(self.stmttrnrs())
        O =  OFX(signonmsgsrsv1=signonmsgsrsv1, bankmsgsrsv1=bankmsgsrsv1)
        document = ET.tostring(O.to_etree()).decode() 
        header = str(make_header(version=220))

        #return '<?xml version="1.0" encoding="UTF-8"?><?OFX OFXHEADER="200" VERSION="220" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>' + header + document
        #return 

        if pretty:
            tree = etree.fromstring((header+document).encode("utf-8"))
            pretty =  etree.tostring(tree, encoding="unicode", pretty_print=True)
            return '<?xml version="1.0" encoding="UTF-8"?>'+"\n"+'<?OFX OFXHEADER="200" VERSION="220" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>' + "\n" + pretty

        return header + document

