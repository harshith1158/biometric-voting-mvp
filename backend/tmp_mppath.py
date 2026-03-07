import mediapipe as mp
import sys
print('mp.__file__=', getattr(mp,'__file__',None))
print('mp.__path__=', getattr(mp,'__path__',None))
print('members=', [m for m in dir(mp) if m.startswith('sol') or m=='__version__'])
print('repr:', repr(mp)[:200])
