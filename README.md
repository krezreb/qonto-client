# Qonto python client

Provides a basic interface for querying and exporting Qonto transactions using the [v2 API](https://api-doc.qonto.com/docs/business-api/ZG9jOjI5NjA5OQ-getting-started)

# Requirements

- python3 with pip


# Installation

```
pip install qonto_client
```

```
git clone https://github.com/krezreb/qonto-client.git
cd qonto-client
pip3 install  --user -r requirements.txt
```

# Configuring Qonto API access

To use the export export scripts, you'll need your Qonto API ID and secret key, available in your Qonto settings.  You'll also need your IBAN, upper case without spaces

Set `ID`, `KEY`, `IBAN` environment variables

```
export ID=your_org-12345
export KEY=YOURSECRETKEY12345678
export IBAN=FR7612345000019876543212345
```

# Exporting to Excel

A script to export to Excel is provided

To Export all transactions:

`python3 export_xlsx.py`

Export all transactions from last month 

`python3 export_xlsx.py --last-month`


# Exporting OFX 

A script to export to OFX is provided, Export all transactions as OFX format

`python3 export_ofx.py`
  
Export all transactions from last month as OFX format

`python3 export_ofx.py --last-month`

All options available via the `--help` command
  
`python3 export_ofx.py --help`
  
# Found a BUG, need a feature?

This project was written over a weekend because of a last minute requirement.  Documentation and features are sketchy.
If you found a problem with the code or want a new feature, Open an issue 🍺 ☕

