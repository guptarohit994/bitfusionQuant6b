from memory import *
import os
import re

def entire_sim_data_parser(filename):
    # if os.path.exists('reconstruct_matrix_temp.txt'):
    #     os.remove('reconstruct_matrix_temp.txt')

    instr_file_pattern = re.compile('^instr_cycle(\d+).txt')

    for file in os.listdir("./cycle_instr_dir/."):
        print(file)
        if instr_file_pattern.match(file):
            print("removing file:{}".format(file))
            os.remove("./cycle_instr_dir/"+file)

    # temp_out_file = open('reconstruct_matrix_temp.txt', 'w')
    cycle_instr_file = ""

    cycle_max = 0
    with open(filename, 'r') as file:
        for line in file:
            line = line.rstrip()
            if "cycle" in line:
                pattern2 = re.compile('^"cycle(\d+)":')
                matches2 = pattern2.match(line)
                assert matches2, 'line is expected to match'
                cycle_max = int(matches2.group(1))

                if cycle_instr_file != "":
                    cycle_instr_file.close()

                cycle_instr_file = open("./cycle_instr_dir/"+'instr_cycle'+matches2.group(1)+".txt", 'w')
                # temp_out_file.write("#cycle"+matches2.group(1)+"\n")
                cycle_instr_file.write("#cycle"+matches2.group(1)+"\n")
            elif "command" in line:
                if "nop" not in line:
                    pattern = re.compile('^.*command": "(.*)"')
                    matches = pattern.match(line)

                    if matches:
                        # temp_out_file.write(matches.group(1)+"\n")
                        cycle_instr_file.write(matches.group(1)+"\n")

    # temp_out_file.close()
    if cycle_instr_file != "":
        cycle_instr_file.close()
    print("total cycles:{}".format(cycle_max))



if __name__ == "__main__":
    in_file_name = 'entire_sim_data.txt'
    if os.path.isfile(in_file_name):
        entire_sim_data_parser(in_file_name)

    # obuf_data = {}
    # total_windows = 4
    # kernel_size = 4
    # bitfusion_cols = 16
    # bitfusion_row = 16
    # obuf_size = 256
    # total_cycles = 1
    #
    # for buf_num in range(bitfusion_cols):
    #     obuf_data['OBUF_x_'+str(buf_num)] = {}
    #     obuf_data['OBUF_x_'+str(buf_num)]['mem_obj'] = memory('OBUF_x_'+str(buf_num), obuf_size, False)
    #
    # cycle = 1
    # window_output = []
    #
    # for win in range(total_windows):
    #     if win == total_windows - 1:
    #         cycle += 1
    #     buf_num_to_access = win % 16
    #     addr_to_load = 0x0 + (4*cycle)
    #     buf_name = 'OBUF_x_'+str(buf_num_to_access)
    #
    #     # data will be a list
    #     data = obuf_data[buf_name]['mem_obj'].load_mem(addr_to_load, 4)
    #     accumulated_num = 0
    #
    #     for x in range(4):
    #         accumulated_num += data[x] << (x*8)
    #
    #     window_output[win] = accumulated_num

