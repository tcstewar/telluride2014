import sys

try:
    bot_index=int(sys.argv[1])
except:
    bot_index=None

addrs = ['10.162.177.43', '10.162.177.44', '10.162.177.55']
freqs = [100, 200, 300]
#freqs = [400, 250, 50]

dir = [-1, 1, 1]

def get_dir():
    if bot_index is None: return 1
    return dir[bot_index]


def get_addr():
    if bot_index is None: return None
    return addrs[bot_index]

def get_self_freq():
    if bot_index is None: return 0
    return freqs[bot_index]

def get_good_freq():
    if bot_index is None: return 0
    return freqs[(bot_index + 1) % len(freqs)]

def get_bad_freq():
    if bot_index is None: return 0
    return freqs[(bot_index + 2) % len(freqs)]


