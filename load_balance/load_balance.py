import os
import platform
import json


machine_config = '/nfs/home/guohongyu/.config/dispatch.json'
machine_threads = 16 # 仿真使用的处理器线程数，应该与编译emu时指定的线程数一致
hostname = "open15" # 在哪个节点上跑仿真

def get_machine_hash(task='xiangshan'):
    hash_ids = {}
    with open(machine_config) as f:
        js = json.load(f)[task]
    cursor = 0
    for host in js:
        hash_ids[host] = []
        for i in range(0, js[host]['load']):
            hash_ids[host].append(cursor)
            cursor += 1
    hostname = platform.node()
    return hash_ids[hostname], cursor

def get_machine_threads(task='xiangshan'):
    with open(machine_config) as f:
        js = json.load(f)[task]
    return int(machine_threads)

def write_dispatch_json(task='xiangshan'):
    hosts = ['open'+'{:02d}'.format(i+1) for i in range(27)]
    print(hosts)
    js = {}
    js[task] = {}
    # open16 - open20
    ryzen_5950x_hosts = ['open'+'{:02d}'.format(i) for i in range(16, 21)]
    # print(ryzen_5950x_hosts)
    epyc_hosts = sorted(list(set(hosts)-set(ryzen_5950x_hosts)))
    # open05 - open11
    # epyc_hosts_to_use = ['open'+'{:02d}'.format(i) for i in range(5, 16)]
    # epyc_hosts_to_use = ['open09']
    # epyc_hosts_to_use = ['open14']
    epyc_hosts_to_use = [hostname]
    # print(epyc_hosts)
    for host in hosts:
        if host not in epyc_hosts_to_use:   
            js[task][host] = {'load': 0, 'threads': 0}
        else:
            js[task][host] = {'load': 10, 'threads': 8}
    
    
    
    with open(machine_config, 'w') as f:
        json.dump(js, f, indent=4)

if __name__ == '__main__':
    write_dispatch_json()




