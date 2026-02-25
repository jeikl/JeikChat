import sys
sys.path.insert(0, ".")
from settings import reload_settings
s = reload_settings()
print("QWEN_MODEL:", repr(s.QWEN_MODEL))
