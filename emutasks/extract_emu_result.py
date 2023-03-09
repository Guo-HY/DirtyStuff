import json
import sh
import os
import re
import subprocess
import sys

py_path = os.path.dirname(os.path.abspath(__file__))

emu_result_dir = sys.argv[1]
# emu_result_dir = "/nfs/home/guohongyu/spec_result/xs_simpoint_batch/SPEC06_EmuTasksConfig_2023-02-03_fdip-64set-8way-icache-newipfbuffer-emu"
# emu_result_dir = "/nfs/home/guohongyu/spec_result/xs_simpoint_batch/SPEC06_EmuTasksConfig_2023-02-01_fdip-128set-8way-icache-noprefetch-emu"
emu_result_file_name = "emu_result.json"

check_multihit_path = f"{py_path}/check_multihit"
os.system(f"g++ {py_path}/check_multihit.cpp -o {check_multihit_path}")
enable_checkmultihit = True

js = {}

if not os.path.exists(emu_result_dir):
  print("error : emu_result_dir not exist")
  exit(1)

benchmarkdirs = os.listdir(emu_result_dir)

total_testpoint_num = 0
aborted_testpoint_num = 0
completed_testpoint_num = 0
completed_but_has_multihit_num = 0
aborted_but_not_has_multihit_num = 0
aborted_and_has_multihit_num = 0

count_ipc_testpoint_num = 0
total_count_ipc = 0

for benchmarkdir in benchmarkdirs:
  if not os.path.isdir(os.path.join(emu_result_dir, benchmarkdir)):
    continue
  js[benchmarkdir] = {}
  testpointdirs = os.listdir(os.path.join(emu_result_dir, benchmarkdir))
  for testpointdir in testpointdirs:
    js[benchmarkdir][testpointdir] = {}
    nowdir = os.path.join(emu_result_dir, benchmarkdir, testpointdir)
    # get ipc info
    ipc = 0
    try:
      ipc = sh.grep("-o", "IPC = [0-9].*[0-9]",
          os.path.join(nowdir, "main_out.txt"))
      js[benchmarkdir][testpointdir]["IPC"] = re.findall(r"[0-9].*[0-9]", str(ipc))[0]
      count_ipc_testpoint_num = count_ipc_testpoint_num + 1
      total_count_ipc = total_count_ipc + float(js[benchmarkdir][testpointdir]["IPC"])
    except Exception as e:
      js[benchmarkdir][testpointdir]["IPC"] = "0"
    # get run state info : aborted or completed
    total_testpoint_num = total_testpoint_num + 1
    runfiles = os.listdir(nowdir)
    if runfiles.count("completed") != 0:
      js[benchmarkdir][testpointdir]["state"] = "completed"
      completed_testpoint_num = completed_testpoint_num + 1
    elif runfiles.count("aborted") != 0:
      js[benchmarkdir][testpointdir]["state"] = "aborted"
      aborted_testpoint_num = aborted_testpoint_num + 1
    elif runfiles.count("running") != 0:
      js[benchmarkdir][testpointdir]["state"] = "running" 
    else :
      js[benchmarkdir][testpointdir]["state"] = "unknown"
      
    js[benchmarkdir][testpointdir]["has-multi-hit"] = "ignore"

    # get multi-hit info
    if enable_checkmultihit:
      r = 0
      r = subprocess.call([f"{check_multihit_path}", f"{nowdir}/main_err.txt",f"/dev/null", f"{nowdir}/icache_err.txt"])
      print(f"finish {nowdir} icache sim, return value = {r}")
      if r & 0x4 != 0:
        js[benchmarkdir][testpointdir]["has-multi-hit"] = "yes"
        if js[benchmarkdir][testpointdir]["state"] == "completed":
          completed_but_has_multihit_num = completed_but_has_multihit_num + 1
        elif js[benchmarkdir][testpointdir]["state"] == "aborted":
          aborted_and_has_multihit_num = aborted_and_has_multihit_num + 1
      elif r == 0:
        js[benchmarkdir][testpointdir]["has-multi-hit"] = "no"
        if js[benchmarkdir][testpointdir]["state"] == "aborted":
          aborted_but_not_has_multihit_num = aborted_but_not_has_multihit_num + 1
      else:
        js[benchmarkdir][testpointdir]["has-multi-hit"] = "Ooops ! there has some probs"

result = {}
result["result"] = js
result["count"] = {
  "total_testpoint_num" : total_testpoint_num,
  "completed_testpoint_num" : completed_testpoint_num,
  "aborted_testpoint_num" : aborted_testpoint_num,
  "completed_but_has_multihit_num" : completed_but_has_multihit_num,
  "aborted_but_not_has_multihit_num" : aborted_but_not_has_multihit_num,
  "aborted_and_has_multihit_num" : aborted_and_has_multihit_num,
  "count_ipc_testpoint_num" : count_ipc_testpoint_num,
  "average_ipc" : 0 if count_ipc_testpoint_num == 0  else total_count_ipc / count_ipc_testpoint_num
}
with open(os.path.join(emu_result_dir, emu_result_file_name), 'w') as f:
  json.dump(result, f, indent=4)

