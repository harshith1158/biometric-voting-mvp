import sys, os

# ensure backend directory is on path so `import app` works
here = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(here, '..')))
