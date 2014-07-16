import sys

bot_index=int(sys.argv[1])

addrs = ['10.162.177.43', '10.162.177.44', '10.162.177.49']
freqs = [100, 200, 300]
freqs = [400, 250, 50]

dir = [1, 1, -1]

def get_dir():
    return dir[bot_index]


def get_addr():
    return addrs[bot_index]

def get_self_freq():
    return freqs[bot_index]

def get_good_freq():
    return freqs[(bot_index + 1) % len(freqs)]

def get_bad_freq():
    return freqs[(bot_index + 2) % len(freqs)]


