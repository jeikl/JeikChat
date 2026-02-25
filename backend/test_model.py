import sys
sys.path.insert(0, ".")
from api.model import get_dynamic_model_options

result = get_dynamic_model_options()
print("Result:", result)
