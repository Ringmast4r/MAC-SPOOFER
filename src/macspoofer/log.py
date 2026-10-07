from datetime import datetime
from .paths import DATA

def write_log(message):
    with (DATA / 'desktop.log').open('a', encoding='utf-8') as f:
        f.write(datetime.now().astimezone().isoformat(timespec='seconds') + ' ' + str(message) + '\n')
