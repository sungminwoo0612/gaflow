# https://docs.cvat.ai/docs/administration/community/basics/installation/
import json
from cvat_sdk import make_client
from datetime import datetime

# --- 설정 ---
CVAT_HOST = "http://localhost:18080"
CVAT_USER = "sm_woo"
CVAT_PASSWORD = "nachotron1"

def extract_custom_metadata(task):
    """
    """