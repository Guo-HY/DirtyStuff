import os


rpt_folder_path = "/nfs/home/guohongyu/dc_example/rptbak"
timing_file_name = "Frontend.timing.rpt"
ext_timing_file_name = "ext." + timing_file_name
path_keywords = ["icache", "itlb", ]

in_f = open(os.path.join(rpt_folder_path, timing_file_name), "r")
out_f = open(os.path.join(rpt_folder_path, ext_timing_file_name), "w")
in_lines = in_f.readlines()

in_group = False
ext_group = False
group_lines = []
ext_group_num = 0
total_group_num = 0

def print_ext_group():
  global ext_group_num
  if ext_group == False:
    return
  ext_group_num = ext_group_num + 1
  for line in group_lines:
    print(line, file=out_f, end="")
  print("-------------------", file=out_f)

for line in in_lines:
  if "Startpoint:" in line:
    total_group_num = total_group_num  + 1
    if in_group == True:
      print_ext_group()
    in_group = True
    ext_group = False
    group_lines.clear()
    
  if in_group == False:
    continue
  
  group_lines.append(line)
  for keyword in path_keywords:
    if keyword in line:
      ext_group = True
      break
    
print("total group num = " + str(total_group_num))
print("total ext group num = " + str(ext_group_num))
in_f.close()
out_f.close()


    
  