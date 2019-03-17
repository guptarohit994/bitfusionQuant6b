from memory import *
import os
import re

if __name__ == "__main__":
    obuf_data = {}
    total_windows = 4
    kernel_size = 4
    bitfusion_cols = 16
    bitfusion_row = 16
    obuf_size = 256
    total_cycles = 1

    for buf_num in range(bitfusion_cols):
        obuf_data['OBUF_x_'+str(buf_num)] = {}
        obuf_data['OBUF_x_'+str(buf_num)]['mem_obj'] = memory('OBUF_x_'+str(buf_num), obuf_size, False)

    cycle = 1
    window_output = []

    for win in range(total_windows):
        if win == total_windows - 1:
            cycle += 1
        buf_num_to_access = win % 16
        addr_to_load = 0x0 + (4*cycle)
        buf_name = 'OBUF_x_'+str(buf_num_to_access)

        # data will be a list
        data = obuf_data[buf_name]['mem_obj'].load_mem(addr_to_load, 4)
        accumulated_num = 0

        for x in range(4):
            accumulated_num += data[x] << (x*8)

        window_output[win] = accumulated_num

