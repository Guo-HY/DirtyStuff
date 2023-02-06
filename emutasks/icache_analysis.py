import os
import json
import matplotlib.pyplot as plt
import numpy as np
import random

base_dir = "/nfs/home/guohongyu/spec_result/xs_simpoint_batch/"
emu_result_name = "emu_result.json"
result_dirs = {
  "SPEC06_EmuTasksConfig_2023-02-03_fdip-64set-8way-icache-newipfbuffer-emu" : "2-3-fdip-64set-8way-newipfbuffer",
  "SPEC06_EmuTasksConfig_2023-01-30_fdip-32kb-prefetch-emu" : "1-30-fdip-32kb-hasprefetch",
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
      alltestpoint_ipc[result_name].append(float(result[benchmark][testpoint]["IPC"]))
    

color = 1600
x = list(range(len(alltestpoint_list)))
alltestpointname = []
for tuple in alltestpoint_list:
  alltestpointname.append(tuple[0] + "-" + tuple[1])
total_width, n = 0.8, len(result_dirs)
width = total_width / n

plt.figure(figsize=(30,24))
color = ['r','g','b']
for result_name in alltestpoint_ipc.keys():
  ipcs = alltestpoint_ipc[result_name]
  t = plt.bar(x, ipcs, width=width, label=result_name, color=color[random.randint(0,len(color)-1)])
  plt.bar_label(t, padding=3)
  for i in range(len(x)):
    x[i] = x[i] + width

plt.ylabel('ipc')
plt.xlabel('testpoint name')
plt.title('icache perf ipc')

plt.xticks(list(range(len(alltestpoint_list))), alltestpointname, rotation=90)
plt.legend()
plt.savefig('ipc.png')