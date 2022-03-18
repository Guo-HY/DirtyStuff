import argparse
import json
import random
from multiprocessing import Pool
from multiprocessing import Value
from ctypes import c_bool
import time

import load_balance as lb
from common import task_blacklist
from common import *
from common.task_tree import task_tree_to_batch_task
from common.simulator_task import task_wrapper, task_wrapper_with_numactl

class CptBatchDescription:
    def __init__(self, data_dir, top_output_dir, ver,
            is_simpoint=False,
            simpoints_file=None,
            is_uniform=True,
            is_sparse_uniform=False,
            ):

        self.task_whitelist = []

        self.data_dir = data_dir
        # self.exe = exe
        self.top_output_dir = top_output_dir
        self.ver = ver

        self.is_uniform = is_uniform
        self.is_sparse_uniform = is_sparse_uniform

        self.is_simpoint = is_simpoint
        self.simpoints_file = simpoints_file

        if is_simpoint:
            with open (simpoints_file) as jf:
                simpoints = json.load(jf)
                print(simpoints)
            for workload in simpoints:
                for key in simpoints[workload]:
                    self.task_whitelist.append(f'{workload}_{key}')

        self._tasks = None
        self.tasks = []

        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-T', '--task', action='store', nargs='+')
        self.parser.add_argument('-W', '--workload', action='store', nargs='+')
        self.parser.add_argument('-D', '--dry-run', action='store_true')

        self.workload_filter = []

        self.task_filter = []
        self.task_blacklist = [f.replace('/', '_') for f in task_blacklist[ver]]

        self.args = None

        self.use_numactl = False
        self.num_numa_nodes = 2
        self.num_physical_cores = 128
        self.numactl_prefixes = []
        self.numactl_status_list = []
        self.numactl_avoid_cores = []
        self.numactl_selected_cores = []

        self.workload_blacklist = []

    def parse_args(self):
        self.args = self.parser.parse_args()
        if not self.args.exe:
            print('you must specify an executable file with --exe!')
            exit()
        self.exe = self.args.exe
        return self.args

    def set_conf(self, Conf, task_name):
        self.task_name = task_name
        if self.is_simpoint:
            assert not self.is_uniform
            self.task_tree = find_nemu_simpoint_cpts(self.data_dir)
        else:
            assert self.is_uniform
            if self.is_sparse_uniform:
                self.task_tree = find_nemu_sparse_uniform_cpts(self.data_dir, self.workload_filter)
            else:
                self.task_tree = find_nemu_uniform_cpts(self.data_dir, self.workload_filter)

        self._tasks = task_tree_to_batch_task(Conf,
                self.task_tree,
                self.exe,
                self.top_output_dir,
                self.task_name)

    def set_task_filter(self):
        if self.args.task is not None:
            self.task_filter = self.args.task
        self.task_filter = [f.replace('/', '_') for f in self.task_filter]

        if self.args.workload is not None:
            self.workload_filter = self.args.workload
            print(self.workload_filter)
    
    def set_workload_blacklist(self, workload_blacklist):
        self.workload_blacklist = workload_blacklist

    def clear_numactl_status(self):
        self.numactl_status_list = [Value(c_bool, lock=True) for i in range(len(self.numactl_prefixes))]
        for st in self.numactl_status_list:
            st.value = False

    def init_numactl_prefixes(self, emu_threads, avoid_cores=None, selected_cores=None):
        assert (avoid_cores is None) ^ (selected_cores is None)

        cores_per_node = int(self.num_physical_cores / self.num_numa_nodes)
        per_node_confs = [[[n, i]
            for i in range(n*cores_per_node,(n+1)*cores_per_node,emu_threads)]
            for n in range(self.num_numa_nodes)]
        confs = []
        for pnc in per_node_confs:
            confs += pnc
        if avoid_cores is not None:
            self.numactl_prefixes = [{'node': node, 'cores': str(core) + '-' + str(core+emu_threads-1)}
                    for [node, core] in confs if core not in avoid_cores]
        else:
            self.numactl_prefixes = [{'node': node, 'cores': str(core) + '-' + str(core+emu_threads-1)}
                    for [node, core] in confs if core in selected_cores]
        # print(self.numactl_prefixes)
        # exit()

    def init_numactl_prefixes_for_smt_warmup(self, emu_threads, avoid_cores=None, selected_cores=None):
        assert (avoid_cores is None) ^ (selected_cores is None)
        for c in range(0, self.num_physical_cores):
            if avoid_cores is not None:
                if c in avoid_cores:
                    continue
            else:
                if c not in selected_cores:
                    continue
            smt_twin = c + self.num_physical_cores
            node = int(c // (self.num_physical_cores/self.num_numa_nodes))
            self.numactl_prefixes.append({'node': node, 'cores': f'{c},{smt_twin}'})

    def set_numactl(self, emu_threads, avoid_cores=None, selected_cores=None, st_emu_with_smt_warmup=False):
        assert (avoid_cores is None) ^ (selected_cores is None)
        self.use_numactl = True
        if not st_emu_with_smt_warmup:
            self.init_numactl_prefixes(emu_threads,
                    avoid_cores = avoid_cores, selected_cores = selected_cores)
        else:
            self.init_numactl_prefixes_for_smt_warmup(emu_threads,
                    avoid_cores = avoid_cores, selected_cores = selected_cores)
        self.clear_numactl_status()

    def filter_tasks(self, hashed=False, n_machines=0, task_type='xiangshan'):
        for task in self._tasks:
            task.cpt_file = self.task_tree[task.workload][task.sub_phase_id]
            # print(task.cpt_file)
            if len(self.task_blacklist):
                if task.code_name in self.task_blacklist:
                    task.valid = False
                    continue

            if len(self.task_blacklist):
                if task.code_name not in self.task_whitelist:
                    task.valid = False
                    continue

            if len(self.workload_filter):
                if task.workload not in self.workload_filter:
                    print(task.workload)
                    print(self.workload_filter)
                    task.valid = False
                    continue

            elif len(self.task_filter):
                task.valid = False
                for task_f in self.task_filter:
                    if task_f in task.cpt_file:
                        task.valid = True
                if not task.valid:
                    continue

            if hashed:
                hash_buckets, n_buckets = lb.get_machine_hash(task_type)
                if hash(task) % n_buckets in hash_buckets:
                    task.valid = True
                else:
                    continue
            
            workload = task.code_name.split('_')[0]
            if workload in self.workload_blacklist:
                print(task.code_name, 'evicted')
                task.valid = False
            if task.code_name not in self.task_whitelist:
                task.valid = False


            if self.args.dry_run:
                task.dry_run = True
            self.tasks.append(task)
        random.shuffle(self.tasks)

    def numactl_run(self):
        def clear_status(self):
            st_l = self.numactl_status_list
            def fn(x: tuple):
                n = x[2]
                st = st_l[n]
                with st.get_lock():
                    # print(f"setting status {n} to false")
                    st.value = False
            return fn

        p = Pool(len(self.numactl_prefixes))
        results = [None for t in self.tasks]
        for i in range(len(self.tasks)):
            print(f"{i}, name {self.tasks[i].code_name}")
            if not self.tasks[i].valid:
                print("not valid, skipped")
                continue
            while True:
                broken = False
                idx = -1
                for node_idx in range(len(self.numactl_prefixes)):
                    st = self.numactl_status_list[node_idx]
                    with st.get_lock():
                        if st.value:
                            continue
                        else:
                            idx = node_idx
                            broken = True
                            st.value = True
                            n = self.numactl_prefixes[node_idx]
                            self.tasks[i].numa_node = n['node']
                            self.tasks[i].cores = n['cores']
                            self.tasks[i].use_numactl = True
                            results[i] = p.apply_async(task_wrapper_with_numactl,
                                                       args=(self.tasks[i], node_idx),
                                                       callback=clear_status(self))
                            break
                if broken:
                    # print(f"the {i}th task applied to worker {idx}")
                    break
                else:
                    # print(f"the {i}th task found no worker to run, sleeping")
                    time.sleep(1)

        p.close()
        p.join()
        for i in range(len(results)):
            results[i] = results[i].get()
        return [(res[0], res[1]) if res[0] is not None else None for res in results]

    def run(self, num_threads, debug=False):
        print(f'Run {len(self.tasks)} tasks with {num_threads} threads')
        if num_threads <= 0:
            return
        if debug:
            task_wrapper(self.tasks[0])
        else:
            if self.use_numactl:
                results = self.numactl_run()
            else:
                p = Pool(num_threads)
                results = p.map(task_wrapper, self.tasks, chunksize=1)
                p.close()
            phases = []
            count = 0
            for res in results:
                if res is not None:
                    print(res)
                    # phases.append(res[1])
                    count += 1
            # print(sorted(phases))
            print(f'Finished {count} simulations')

