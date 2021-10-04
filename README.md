# Qonto python client

Provides a basic interface for querying and exporting Qonto transactions

# Requirements

- python3 with pip


# Installation

pip3 install  --user -r requirements.txt

# Usage

Go to this URL to get your api Key and Secret key
https://app.qonto.com/organizations/<your organization>/settings/integrations

You'll also need your IBAN, upper case without spaces

```
export ID=your_org-id-12345
export KEY=YOURSECRETKEY12345678
export IBAN=FR7612345000019876543212345
```

Export all transactions as OFX format

`python3 export_ofx.py --attachments `
