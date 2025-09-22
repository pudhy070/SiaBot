import json
import os

DATA_DIR = 'data'
INVITE_LINKS_FILE = os.path.join(DATA_DIR, 'invite_links.json')

INVITE_LINKS = {}

def load_invite_links():
    global INVITE_LINKS
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if os.path.exists(INVITE_LINKS_FILE):
        with open(INVITE_LINKS_FILE, 'r', encoding='utf-8') as f:
            try:
                loaded_data = json.load(f)
                INVITE_LINKS = {str(k): v for k, v in loaded_data.items()}
            except json.JSONDecodeError:
                INVITE_LINKS = {}
    else:
        INVITE_LINKS = {}
    
    print(f"✅ {len(INVITE_LINKS)}개의 서버 초대 링크 로드 완료.")


def save_invite_links():
    with open(INVITE_LINKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(INVITE_LINKS, f, ensure_ascii=False, indent=4)