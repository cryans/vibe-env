import requests
import json
from pathlib import Path

headers = {'Content-type': 'application/json'}
if False:
    data = json.dumps({"seriesid": ['CUUR0000SA0','SUUR0000SA0'],"startyear":"2011",
 "endyear":"2014"})
    p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data
, headers=headers)
else:
    p = requests.get('https://api.bls.gov/publicAPI/v2/surveys')
Path('../data/internet/bls/surveys.json').write_text(p.text)

#https://api.bls.gov/publicAPI/v2/timeseries/popular?survey=LA

docs = """Understanding the "Positional" Format
Let's break down the ID you provided: LAUCN040010000000005

LA: Survey Code (Local Area Unemployment Statistics)

U: Seasonal Adjustment (U = Unadjusted)

C: Area Type (C = County)

N04001: FIPS Code (State 04: Arizona, County 001: Apache County)

000000: Industry/Occupation (Not used for this survey)

05: Data Type (Rate: Unemployment)"""

"""https://download.bls.gov/pub/time.series/"""
