import os
import json
import matplotlib.pyplot as plt
import numpy as np
import random
import sys

target_name = sys.argv[1]
base_dir = "/nfs/home/guohongyu/spec_result/xs_simpoint_batch/"
emu_result_name = "emu_result.json"
result_dirs = {
  # "SPEC06_EmuTasksConfig_2023-02-06_fdip-64set-8way-icache-noprefetch-emu" : "64set-8way-noprefetch-hasalias",
  # "SPEC06_EmuTasksConfig_2023-02-14_fdip-64set-8way-icache-solvealias-hasprefetch-emu" : "64set-8way-hasprefetch-noalias",
  # "SPEC06_EmuTasksConfig_2023-02-01_fdip-128set-8way-icache-noprefetch-emu" : "128set-8way-noprefetch-hasalias",
  # "SPEC06_EmuTasksConfig_2023-02-10_fdip-128set-8way-icache-solvealias-emu" : "128set-8way-noprefetch-noalias",
  # "SPEC06_EmuTasksConfig_2023-02-15_fdip-128set-8way-icache-solvealias-hasprefetch-emu" : "128set-8way-hasprefetch-noalias",
  # "SPEC06_EmuTasksConfig_2023-03-03_migrate-hasprefetch-64set-8way-emu" : "64set-8way-hsaprefetch-migrate-master",
  "SPEC06_EmuTasksConfig_2023-05-22_5-22-no-prefetch" : "128set-8way-noprefetch",
  "SPEC06_EmuTasksConfig_2023-05-18_5-18-prefetch-to-L2" : "128set-8way-prefetch-to-L2",
  "SPEC06_EmuTasksConfig_2023-05-21_5-21-prefetch-to-L1" : "128set-8way-prefetch-to-L1",
}

alltestpoint_set = set()
# 先提取出来所有的testpoint name
for result_dir in result_dirs.keys():
  result_name = result_dirs[result_dir]
  fp = open(os.path.join(base_dir, result_dir, emu_result_name))
  emu_result = json.load(fp)
  result = emu_result['result']
  for benchmark in result.keys():
    for testpoint in result[benchmark].keys():
      testpoint_name = (benchmark,testpoint)
      alltestpoint_set.add(testpoint_name)

alltestpoint_list = list(alltestpoint_set)
alltestpoint_ipc = {}

for result_dir in result_dirs.keys():
  result_name = result_dirs[result_dir]
  alltestpoint_ipc[result_name] = []
  fp = open(os.path.join(base_dir, result_dir, emu_result_name))
  emu_result = json.load(fp)
  result = emu_result['result']
  for tuple in alltestpoint_list:
    benchmark, testpoint = tuple
    if result[benchmark][testpoint]["state"] != "completed":
      alltestpoint_ipc[result_name].append(0)
    else:
      alltestpoint_ipc[result_name].append(float(result[benchmark][testpoint][target_name]))
    

x = list(range(len(alltestpoint_list)))
alltestpointname = []
for tuple in alltestpoint_list:
  alltestpointname.append(tuple[0] + "-" + tuple[1])
total_width, n = 0.8, len(result_dirs)
width = total_width / n

plt.figure(figsize=(30,24))
color = ['#00CED1','#008080', '#D2B48C','#FF8C00','#8B4513', '#800000', '']
color_ptr = 0
for result_name in alltestpoint_ipc.keys():
  ipcs = alltestpoint_ipc[result_name]
  t = plt.bar(x, ipcs, width=width, label=result_name, color=color[color_ptr])
  color_ptr = color_ptr + 1
  plt.bar_label(t, padding=3, fmt='%.2f')
  for i in range(len(x)):
    x[i] = x[i] + width

plt.ylabel(target_name)
plt.xlabel('testpoint name')
plt.title('icache perf ' + target_name)

plt.xticks(list(range(len(alltestpoint_list))), alltestpointname, rotation=90)
plt.legend()
plt.savefig(target_name + '.png')