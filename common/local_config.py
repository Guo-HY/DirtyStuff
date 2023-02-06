import os
import platform
import json


gem5_cpt_top = '/nfs-nvme/home/share/checkpoints_profiles/'
emu_cpt_top = '/nfs-nvme/home/share/checkpoints_profiles/'

if 'Local_Cpt_Top' in os.environ:
    cpt_top = os.environ['Local_Cpt_Top']
    print(f'Set local cpt top to {cpt_top}')
else:
    cpt_top = emu_cpt_top

if 'Local_Result_Top' in os.environ:
    local_result_top = os.environ['Local_Result_Top']
    print(f'Set local result top to {local_result_top}')
else:
    local_result_top = '/no/where'

if 'Shared_Result_Top' in os.environ:
    shared_result_top = os.environ['Shared_Result_Top']
else:
    shared_result_top = '/nfs/home/guohongyu/shared_spec_result'

# /path/to/spec2006/benchspec/CPU2006
spec_cpu_2006_dir = '/no/where'
if 'cpu_2006_dir' in os.environ:
    spec_cpu_2006_dir = os.environ['cpu_2006_dir']

# /path/to/spec2017/benchspec/CPU
spec_cpu_2017_dir = '/no/where'
if 'cpu_2017_dir' in os.environ:
    spec_cpu_2017_dir = os.environ['cpu_2017_dir']

gathered_spec2017_data_dir = '/no/where'
if 'spec2017_run_dir' in os.environ:
    gathered_spec2017_data_dir = os.environ['spec2017_run_dir']

gathered_spec2006_data_dir = '/no/where'
if 'spec2006_run_dir' in os.environ:
    gathered_spec2006_data_dir = os.environ['spec2006_run_dir']

simpoints_file = {
        '17': 'resources/simpoint_cpt_desc/simpoints17.json',
        '06': 'resources/simpoint_cpt_desc/simpoints06.json',
        }

simpoints_file_short = {
        '17': '/no/where',
        '06': 'resources/simpoint_cpt_desc/simpoints06_cover0.5.json', # 231 points
        }

