#!/usr/bin/env python
"""Test RD Service CAPTURE method connectivity"""
import requests
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS')

# Try both ports
ports = [11100, 11200]
protocols = ['http', 'https']

for protocol in protocols:
    for port in ports:
        try:
            url = f'{protocol}://127.0.0.1:{port}/rd/capture'
            payload = '''<PidOptions ver="1.0">
<Opts fCount="1" fType="0" iCount="0" iType="0" pCount="0" format="0" pidVer="2.0" timeout="10000" otp="" wadh="" posh="UNKNOWN" env="P"/>
<CustOpts/>
</PidOptions>'''
            
            print(f"\nTesting {protocol.upper()} CAPTURE on {url}...")
            r = requests.request(
                method='CAPTURE',
                url=url,
                data=payload,
                headers={'Content-Type': 'text/xml'},
                timeout=3,
                verify=False
            )
            print(f'  ✓ Status: {r.status_code}')
            print(f'  ✓ Response: {r.text[:200]}...')
        except requests.exceptions.ConnectTimeout:
            print(f'  ✗ Connection Timeout')
        except requests.exceptions.ConnectionError as e:
            print(f'  ✗ Connection Error')
        except requests.exceptions.Timeout:
            print(f'  ✗ Read Timeout')
        except Exception as e:
            print(f'  ✗ {type(e).__name__}: {str(e)[:100]}')

