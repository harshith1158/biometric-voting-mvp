import argparse
import requests

parser = argparse.ArgumentParser(description="Send a selfie to the liveness endpoint")
parser.add_argument('image', nargs='?', default='tmp_selfie.jpg',
                    help='Path to image file (JPEG/PNG)')
parser.add_argument('--voter', default='123e4567-e89b-12d3-a456-426614174000',
                    help='Voter UUID to submit')
args = parser.parse_args()

with open(args.image, 'rb') as f:
    r = requests.post('http://127.0.0.1:5000/api/biometrics/selfie',
                      data={'voter_id': args.voter},
                      files={'image': f})

print('STATUS', r.status_code)
try:
    print(r.json())
except Exception:
    print(r.text)
