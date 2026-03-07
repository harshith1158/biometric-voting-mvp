import argparse
import traceback
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description="Run /api/biometrics/selfie via Flask test client")
parser.add_argument('image', nargs='?', default='tmp_selfie.jpg',
                    help='Path to image file to send')
parser.add_argument('--voter', default='123e4567-e89b-12d3-a456-426614174000',
                    help='UUID to send as voter_id')
args = parser.parse_args()

try:
    # ensure project root on sys.path
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))

    import app.main as main_mod
    # get Flask app: prefer `create_app()` then `app` attribute
    app = None
    if hasattr(main_mod, 'create_app'):
        app = main_mod.create_app()
    elif hasattr(main_mod, 'app'):
        app = main_mod.app
    else:
        raise RuntimeError('Could not find Flask app in app.main')

    client = app.test_client()
    img_path = Path(args.image)
    if not img_path.exists():
        print(f'{img_path} not found')
        sys.exit(2)

    with open(img_path, 'rb') as f:
        # Flask test client accepts file tuples: (fileobj, filename)
        data = {
            'voter_id': args.voter,
            'image': (f, img_path.name),
        }
        rv = client.post('/api/biometrics/selfie', data=data, follow_redirects=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)
else:
    try:
        # Try to print response info
        print('STATUS', rv.status_code)
        print(rv.get_data(as_text=True))
    except Exception:
        traceback.print_exc()
        sys.exit(1)
