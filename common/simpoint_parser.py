# This file is copied from gem5 for parsing simpoint outputs
import re


# Set up environment for taking SimPoint checkpoints
# Expecting SimPoint files generated by SimPoint 3.2
def parse_simpoint_analysis_file(simpoint_filename, weight_filename, interval_length, warmup_length):
    # print("simpoint analysis file:", simpoint_filename)
    # print("simpoint weight file:", weight_filename)
    # print("interval length:", interval_length)
    # print("warmup length:", warmup_length)

    interval_length = int(interval_length)
    warmup_length = int(warmup_length)

    # Simpoint analysis output starts interval counts with 0.
    simpoints = []
    simpoint_start_insts = []

    # Read in SimPoint analysis files
    simpoint_file = open(simpoint_filename)
    weight_file = open(weight_filename)
    while True:
        line = simpoint_file.readline()
        if not line:
            break
        m = re.match("(\d+)\s+(\d+)", line)
        if m:
            interval = int(m.group(1))
        else:
            fatal('unrecognized line in simpoint file!')

        line = weight_file.readline()
        if not line:
            fatal('not enough lines in simpoint weight file!')
        m = re.match("([0-9\.e\-]+)\s+(\d+)", line)
        if m:
            weight = float(m.group(1))
        else:
            fatal('unrecognized line in simpoint weight file!')

        if (interval * interval_length - warmup_length > 0):
            starting_inst_count = \
                interval * interval_length - warmup_length
            actual_warmup_length = warmup_length
        else:
            # Not enough room for proper warmup
            # Just starting from the beginning
            starting_inst_count = 0
            actual_warmup_length = interval * interval_length

        simpoints.append((interval, weight, starting_inst_count,
            actual_warmup_length))

    # Sort SimPoints by starting inst count
    simpoints.sort(key=lambda obj: obj[2])
    for s in simpoints:
        interval, weight, starting_inst_count, actual_warmup_length = s
        # print(str(interval), str(weight), starting_inst_count,
        #     actual_warmup_length)
        simpoint_start_insts.append(starting_inst_count)

    # print("Total # of simpoints:", len(simpoints))

    return simpoints
