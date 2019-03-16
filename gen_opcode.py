import numpy as np
from memory import *
import json
import os
import psutil
from pprint import pprint
import re


class gen_op_code():
    # bitfusion_dim is a tuple indicating how many rows and columns in bitfusiont
    def __init__(self, input_image, kernel, bitfusion_dim=(4,4), bitbrick_dim=(4,4),\
                 ibuf_size=256, wbuf_size=128, obuf_size=16*1024,\
                 input_quantization=8, weight_quantization=8):
        self.input_image = input_image
        self.kernel = kernel
        self.entire_sim_data = {}
        self.entire_mem_data = {}
        # indicates how may windows are possible
        self.window_num = 0
        self.cycles_used = 0
        self.input_image_shape = list(self.input_image.shape)
        self.kernel_shape = list(self.kernel.shape)
        # tells how many fusionUnits inside bitFusion
        self.bitFusion_rows = bitfusion_dim[0]
        self.bitFusion_cols = bitfusion_dim[1]
        # tells how many bitBricks inside a fusionUnit
        self.bitBrick_rows = bitbrick_dim[0]
        self.bitBrick_cols = bitbrick_dim[1]
        self.ibuf_size = ibuf_size
        self.wbuf_size = wbuf_size
        self.obuf_size = obuf_size
        self.inputQuantization = input_quantization
        self.weightQuantization = weight_quantization


        self.init_buffers_in_mem_db(self.bitFusion_rows, self.bitFusion_cols)

    def init_buffers_in_mem_db(self, fu_in_rows, fu_in_cols):
        # TODO check if capacity of buffer finished
        for r in range(fu_in_rows):
            for c in range(fu_in_cols):
                ibuf_name = 'IBUF_'+str(r)+"_"+str(c)
                wbuf_name = 'WBUF_'+str(r)+"_"+str(c)
                self.entire_mem_data[ibuf_name] = {}
                self.entire_mem_data[ibuf_name]['all_lru'] = []

                input_image_pixel_size = self.input_image_shape[0] * self.input_image_shape[1]
                if len(self.input_image_shape)== 3:
                    input_image_pixel_size *= self.input_image_shape[2]
                for byte16 in range(int(self.ibuf_size/16)):
                    if input_image_pixel_size > byte16*16:
                        self.entire_mem_data[ibuf_name]['mem'+str(byte16*16)] = {}
                        self.entire_mem_data[ibuf_name]['mem'+str(byte16*16)]['pix_byte'] = byte16*16
                        self.entire_mem_data[ibuf_name]['mem'+str(byte16*16)]['lru'] = 0
                        self.entire_mem_data[ibuf_name]['all_lru'].append(0)
                        self.entire_mem_data[ibuf_name]['pix'+str(byte16*16)] = byte16*16
                    else:
                        self.entire_mem_data[ibuf_name]['mem'+str(byte16*16)] = {}
                        self.entire_mem_data[ibuf_name]['mem'+str(byte16*16)]['pix_byte'] = 0
                        self.entire_mem_data[ibuf_name]['mem'+str(byte16*16)]['lru'] = 0
                        self.entire_mem_data[ibuf_name]['all_lru'].append(0)
                        self.entire_mem_data[ibuf_name]['pix'+str(byte16*16)] = byte16*16

                self.entire_mem_data[wbuf_name] = {}
                self.entire_mem_data[wbuf_name]['all_lru'] = []
                input_kernel_pixel_size = self.kernel_shape[0] * self.kernel_shape[1]
                if len(self.kernel_shape) == 3:
                    input_kernel_pixel_size *= self.kernel_shape[2]

                for byte16 in range(int(self.wbuf_size/16)):
                    if input_kernel_pixel_size < self.wbuf_size and input_kernel_pixel_size > byte16*16:
                        self.entire_mem_data[wbuf_name]['mem'+str(byte16*16)] = {}
                        self.entire_mem_data[wbuf_name]['mem'+str(byte16*16)]['pix_byte'] = byte16
                        self.entire_mem_data[wbuf_name]['mem'+str(byte16*16)]['lru'] = 0
                        self.entire_mem_data[wbuf_name]['all_lru'].append(0)
                        self.entire_mem_data[wbuf_name]['pix'+str(byte16*16)] = byte16*16
                    else:
                        self.entire_mem_data[wbuf_name]['mem'+str(byte16*16)] = {}
                        self.entire_mem_data[wbuf_name]['mem'+str(byte16*16)]['pix_byte'] = 0
                        self.entire_mem_data[wbuf_name]['mem'+str(byte16*16)]['lru'] = 0
                        self.entire_mem_data[wbuf_name]['all_lru'].append(0)
                        self.entire_mem_data[wbuf_name]['pix'+str(byte16*16)] = byte16*16

        for c in range(fu_in_cols):
            obuf_name = 'OBUF_x_'+str(c)
            self.entire_mem_data[obuf_name] = {}
            self.entire_mem_data[obuf_name]['next_byte'] = 0

    def init_cycle_in_db(self, cycle_num):
        new_cycle_num = cycle_num
        new_cycle_name = 'cycle'+str(new_cycle_num)
        assert new_cycle_name not in self.entire_sim_data.keys(), 'gen_opcode.py <- init_cycle_in_db: cycle already present'
        self.entire_sim_data[new_cycle_name] = {}

        for col in range(self.bitFusion_cols):
            col_name = "col"+str(col)
            self.entire_sim_data[new_cycle_name][col_name] = {}
            self.entire_sim_data[new_cycle_name][col_name]['nextFU'] = 'FU_0_' + str(col)
            self.entire_sim_data[new_cycle_name][col_name]['status'] = 'free'
            self.entire_sim_data[new_cycle_name][col_name]['command'] = "nop"

            for row in range(self.bitFusion_rows):
                fu_name = 'FU_'+str(row)+"_"+str(col)
                self.entire_sim_data[new_cycle_name][col_name][fu_name] = {}
                self.entire_sim_data[new_cycle_name][col_name][fu_name]['status'] = 'free'

                for row_bb in range(self.bitBrick_rows):
                    for col_bb in range(self.bitBrick_cols):
                        bb_name = 'BB_' + str(row_bb) + "_" + str(col_bb)
                        self.entire_sim_data[new_cycle_name][col_name][fu_name][bb_name] = {}
                        self.entire_sim_data[new_cycle_name][col_name][fu_name][bb_name]['status'] = 'free'
                        self.entire_sim_data[new_cycle_name][col_name][fu_name][bb_name]['command'] = "nop"



    def clear_cycle_from_sim_data(self, cycle_remove):
        with open('entire_sim_data.txt', 'a+') as file:
            file.write(cycle_remove)
            #pprint(self.entire_sim_data[cycle_remove], stream=file, indent=4)
            file.write(json.dumps(self.entire_sim_data[cycle_remove], indent=4))  # use `json.loads` to do the reverse
            file.write("\n")
        self.entire_sim_data.pop(cycle_remove, None)

    def clear_full_obuf_data(self, obuf_name):
        with open(obuf_name+".txt", 'a+') as file:
            file.write(obuf_name+"\n")
            file.write(json.dumps(self.entire_mem_data[obuf_name], indent=4))
            file.write("\n")

        obuf_keys = list(self.entire_mem_data[obuf_name].keys())
        for key in obuf_keys:
            if key == 'next_byte':
                continue
            else:
                self.entire_mem_data[obuf_name].pop(key, None)

    # adds new cycle to the DB but removes data of previous cycles into a file
    def add_new_cycle(self):
        if self.cycles_used > 0:
            cycle_remove = 'cycle'+str(self.cycles_used)
            self.clear_cycle_from_sim_data(cycle_remove)

        self.cycles_used += 1
        self.init_cycle_in_db(self.cycles_used)

    # gives a usable column for a kernel to use
    # also spits out address for accumulator of that column
    def get_usable_bitfusion_col(self, window_num):
        cur_cycle = self.cycles_used

        for colNum in range(self.bitFusion_cols):
            if self.entire_sim_data['cycle'+str(cur_cycle)]['col'+str(colNum)]['status'] == 'free':
                self.entire_sim_data['cycle' + str(cur_cycle)]['col' + str(colNum)]['status'] = 'used'
                # print("gen_opcode.py <- get_usable_bitfusion_col= window:{} can be accomodated in cycle:{} at col:{}".\
                #      format(window_num, self.cycles_used, colNum))

                self.gen_staddr_cmd(colNum, 'col'+str(colNum), cur_cycle)
                return cur_cycle, colNum

        # if reached here, it means next cycle needed
        self.add_new_cycle()
        cur_cycle = self.cycles_used
        for colNum in range(self.bitFusion_cols):
            if self.entire_sim_data['cycle'+str(cur_cycle)]['col'+str(colNum)]['status'] == 'free':
                self.entire_sim_data['cycle' + str(cur_cycle)]['col' + str(colNum)]['status'] = 'used'
                # print("gen_opcode.py <- get_usable_bitfusion_col= window:{} can be accomodated in cycle:{} at col:{}".\
                #      format(window_num, self.cycles_used, colNum))
                self.gen_staddr_cmd(colNum, 'col'+str(colNum), cur_cycle)
                return cur_cycle, colNum

    def get_fusion_unit_status_from_quantization(self, cycle_num, col_num, fu_name):
        cycle_name = 'cycle'+str(cycle_num)
        col_name = 'col'+str(col_num)
        pair_value = (self.inputQuantization, self.weightQuantization)

        # status = free, top_right_used, top_used, bottom_right_used, used
        if pair_value in [(8,8), (8,6), (6,8), (6,6)]:
            if self.entire_sim_data[cycle_name][col_name][fu_name]['status'] == 'used':
                return 'free'
            else:
                return 'used'
        elif pair_value in [(8,4), (4,8), (8,2), (2,8), (6,4), (4,6)]:
            if self.entire_sim_data[cycle_name][col_name][fu_name]['status'] == 'free':
                return 'top_used'
            elif self.entire_sim_data[cycle_name][col_name][fu_name]['status'] == 'top_used':
                return 'used'
        elif pair_value in [(5,5)]:
            if self.entire_sim_data[cycle_name][col_name][fu_name]['status'] == 'free':
                return 'bottom_right_used'
            elif self.entire_sim_data[cycle_name][col_name][fu_name]['status'] == 'bottom_right_used':
                return 'used'
        elif pair_value in [(6,2), (2,6), (4,4), (4,2), (2,2)]:
            if self.entire_sim_data[cycle_name][col_name][fu_name]['status'] == 'free':
                return 'top_right_used'
            elif self.entire_sim_data[cycle_name][col_name][fu_name]['status'] == 'top_right_used':
                return 'top_used'
            elif self.entire_sim_data[cycle_name][col_name][fu_name]['status'] == 'top_used':
                return 'bottom_right_used'
            elif self.entire_sim_data[cycle_name][col_name][fu_name]['status'] == 'bottom_right_used':
                return 'used'



    # when quantized to sub-byte levels, order of filling a bitBrick is
    # top-right -> top-left -> bottom-right -> bottom-left
    def get_usable_fusion_unit(self, col, window_num):
        cur_cycle = self.cycles_used
        cycle_name = 'cycle'+str(cur_cycle)
        col_name = 'col'+str(col)

        for rowNum in range(self.bitFusion_rows):
            fu_name = 'FU_'+str(rowNum)+"_"+str(col)
            if self.entire_sim_data[cycle_name][col_name][fu_name]['status'] != 'used':
                self.entire_sim_data[cycle_name][col_name][fu_name]['status'] = self.get_fusion_unit_status_from_quantization(cur_cycle, col, fu_name)
                return cur_cycle, col, rowNum

        # if reached here, it means next column is needed
        cur_cycle, newCol = self.get_usable_bitfusion_col(window_num)
        cycle_name = 'cycle'+str(cur_cycle)
        col_name = 'col'+str(newCol)

        for rowNum in range(self.bitFusion_rows):
            fu_name = 'FU_'+str(rowNum)+"_"+str(newCol)
            if self.entire_sim_data[cycle_name][col_name][fu_name]['status'] == 'free':
                self.entire_sim_data[cycle_name][col_name][fu_name]['status'] = self.get_fusion_unit_status_from_quantization(cur_cycle, newCol, fu_name)
                return cur_cycle, newCol, rowNum

    def get_mem_loc_to_store_col_accumulated(self, col, cycle):
        obuf_name = 'OBUF_x_'+str(col)
        avail_byte_loc = self.entire_mem_data[obuf_name]['next_byte']

        # TODO check what is '4' below dependent on
        self.entire_mem_data[obuf_name][avail_byte_loc] = {}
        # self.entire_mem_data[obuf_name][avail_byte_loc]['data'] = "from level2 adder of column:"+str(col)
        self.entire_mem_data[obuf_name][avail_byte_loc]['cycle'] = cycle
        self.entire_mem_data[obuf_name]['next_byte'] += 4
        # if obuf is now full,
        if len(self.entire_mem_data[obuf_name].keys()) - 1 == self.obuf_size/4:
            print("TODO: {} is full now in cycles:{}".format(obuf_name, cycle))
            self.clear_full_obuf_data(obuf_name)
        return avail_byte_loc

    def gen_staddr_cmd(self, col, col_name, cycle):
        byte_loc_to_store_in_obuf = self.get_mem_loc_to_store_col_accumulated(col, cycle)
        self.entire_sim_data['cycle'+str(cycle)][col_name]['command'] = 'staddr OBUF_x_'+str(col)+" "+hex(byte_loc_to_store_in_obuf)
        print('staddr OBUF_x_'+str(col)+" "+hex(byte_loc_to_store_in_obuf))


    def get_mem_loc_of_product(self, col, row, fu_name, inp, weight, cycle):
        # TODO check if the memory buf limit is exceeded
        ibuf_name = 'IBUF_'+str(row)+"_"+str(col)
        ibuf_byte_to_place_at = self.entire_mem_data[ibuf_name]['next_byte']
        self.entire_mem_data[ibuf_name][ibuf_byte_to_place_at] = {}
        self.entire_mem_data[ibuf_name][ibuf_byte_to_place_at]['data'] = inp
        self.entire_mem_data[ibuf_name][ibuf_byte_to_place_at]['cycle'] = cycle
        self.entire_mem_data[ibuf_name]['next_byte'] += 1

        wbuf_name = 'WBUF_'+str(row)+"_"+str(col)
        wbuf_byte_to_place_at = self.entire_mem_data[wbuf_name]['next_byte']
        self.entire_mem_data[wbuf_name][wbuf_byte_to_place_at] = {}
        self.entire_mem_data[wbuf_name][wbuf_byte_to_place_at]['data'] = weight
        self.entire_mem_data[wbuf_name][wbuf_byte_to_place_at]['cycle'] = cycle
        self.entire_mem_data[wbuf_name]['next_byte'] += 1

        # TODO insert load from main memory to the above byte locations
        return ibuf_byte_to_place_at, wbuf_byte_to_place_at

    def check_byte_in_buf(self, buf_name, starting_pixel_byte):
        if "pix"+str(starting_pixel_byte) in self.entire_mem_data[buf_name].keys():
            byte_in_mem = self.entire_mem_data[buf_name]['pix'+str(starting_pixel_byte)]

            # update lru
            self.entire_mem_data[buf_name]['all_lru'] = []
            for key in self.entire_mem_data[buf_name]:
                if "mem" in key:
                    if key == 'mem'+str(byte_in_mem):
                        self.entire_mem_data[buf_name][key]['lru'] = 0
                        self.entire_mem_data[buf_name]['all_lru'].append(self.entire_mem_data[buf_name][key]['lru'])
                    else:
                        self.entire_mem_data[buf_name][key]['lru'] += 1
                        self.entire_mem_data[buf_name]['all_lru'].append(self.entire_mem_data[buf_name][key]['lru'])


            return self.entire_mem_data[buf_name]['pix'+str(starting_pixel_byte)]
        else:
            # TODO spit out instr for load from mem to bufa
            print("Need to access 4B starting from {} in {}".format(starting_pixel_byte, buf_name))
            list.sort(self.entire_mem_data[buf_name]['all_lru'], reverse=True)
            max_lru = self.entire_mem_data[buf_name]['all_lru'].pop(0)
            return_mem_location = 0

            replace_done = 0
            self.entire_mem_data[buf_name]['all_lru'] = []
            temp_keys = list(self.entire_mem_data[buf_name].keys())

            for key in temp_keys:
                if "mem" in key:
                    # just do the replace once
                    # if same many have the highest LRU as same, the one with lower byte would be evicted
                    if self.entire_mem_data[buf_name][key]['lru'] == max_lru and replace_done == 0:
                        replace_done = 1
                        # this is the key to replace
                        pixel = self.entire_mem_data[buf_name][key]['pix_byte']
                        print("Evicting from {} at {} which currently has pixel_byte:{}".format(buf_name,key, pixel))
                        self.entire_mem_data[buf_name].pop('pix'+str(pixel), None)

                        pattern = re.compile('mem(\d+)')
                        matches = pattern.match(key)
                        assert matches, 'gen_opcode.py <- check_byte_in_buf: no match found'
                        mem_location = int(matches.group(1))
                        return_mem_location = mem_location
                        self.entire_mem_data[buf_name]['pix'+str(starting_pixel_byte)] = mem_location
                        self.entire_mem_data[buf_name]['mem'+str(mem_location)]['pix_byte'] = starting_pixel_byte
                        self.entire_mem_data[buf_name]['mem'+str(mem_location)]['lru'] = 0
                        self.entire_mem_data[buf_name]['all_lru'].append(self.entire_mem_data[buf_name]['mem'+str(mem_location)]['lru'])

                    else:
                        self.entire_mem_data[buf_name][key]['lru'] += 1
                        self.entire_mem_data[buf_name]['all_lru'].append(self.entire_mem_data[buf_name][key]['lru'])
            return return_mem_location

    def get_ibuf_address_for_coordinates(self, image_num, image_row_coor, image_col_coor, col, row):
        if len(self.input_image_shape) == 3:
            num_bytes = (image_num * self.input_image_shape[1] * self.input_image_shape[2]) + \
                        (self.input_image_shape[2] * image_row_coor) + \
                        (image_col_coor)
        elif len(self.input_image_shape) == 2:
            # single image
            num_bytes = (self.input_image_shape[1] * image_row_coor) + image_col_coor
        else:
            assert 0 > 1, 'gen_opcode.py - get_ibuf_address_for_coordinates: unhandled case'

        # aligned to 16B accesses stores to ibuf
        num_bytes_aligned = int(num_bytes/16) * 16

        # now check if it exists in buf
        ibuf_name = 'IBUF_'+str(row)+"_"+str(col)
        # print("need to find address of pixel:{} in {} and aligned to 16B is:{}".format(num_bytes, ibuf_name, num_bytes_aligned))
        mem_location = self.check_byte_in_buf(ibuf_name, num_bytes_aligned) + (num_bytes%16)
        return mem_location

    def get_wbuf_address_for_coordinates(self, kernel_num, kernel_row_coor, kernel_col_coor, col, row):
        if len(self.kernel_shape) == 3:
            num_bytes = (kernel_num * self.kernel_shape[1] * self.kernel_shape[2]) + \
                        (self.kernel_shape[2] * kernel_row_coor) + \
                        (kernel_col_coor)
        elif len(self.kernel_shape) == 2:
            # single image
            num_bytes = (self.kernel_shape[1] * kernel_row_coor) + kernel_col_coor
        else:
            assert 0 > 1, 'gen_opcode.py - get_wbuf_address_for_coordinates: unhandled case'

        # aligned to 16B accesses stores to ibuf
        num_bytes_aligned = int(num_bytes/16)

        # now check if it exists in buf
        wbuf_name = 'WBUF_'+str(row)+"_"+str(col)
        # print("need to find address of weight:{} in {} and aligned to 16B is:{}".format(num_bytes, wbuf_name, num_bytes_aligned))
        mem_location = self.check_byte_in_buf(wbuf_name, num_bytes_aligned) + (num_bytes%16)
        return mem_location

    def generate_bitBricks_usage_pattern(self, cycle_name, col_name, fu_name):
        input_pair = (self.inputQuantization, self.weightQuantization)
        status = self.entire_sim_data[cycle_name][col_name][fu_name]['status']
        assert status in ['free', 'top_right_used', 'top_used', 'bottom_right_used', 'used'], 'gen_opcode.py - illegal FU status found'
        shift_combination = [[0 for x in range(self.bitBrick_cols)] for y in range(self.bitBrick_rows)]
        if input_pair == (8, 8):
            shift_combination = [[(0, 6), (0, 4), (0, 2), (0, 0)],
                                 [(2, 6), (2, 4), (2, 2), (2, 0)],
                                 [(4, 6), (4, 4), (4, 2), (4, 0)],
                                 [(6, 6), (6, 4), (6, 2), (6, 0)]]
        elif input_pair == (8, 6):
            shift_combination = [[(6, 0), (4, 0), (2, 0), (0, 0)],
                                 [(6, 2), (4, 2), (2, 2), (0, 2)],
                                 [(6, 4), (4, 4), (2, 4), (0, 4)],
                                 [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
        elif input_pair == (8, 4):
            if status == 'top_used':
                shift_combination = [[(6, 0), (4, 0), (2, 0), (0, 0)],
                                    [(6, 2), (4, 2), (2, 2), (0, 2)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(6, 0), (4, 0), (2, 0), (0, 0)],
                                    [(6, 2), (4, 2), (2, 2), (0, 2)]]
        elif input_pair == (8, 2):
            if status == 'top_used':
                shift_combination = [[(6, 0), (4, 0), (2, 0), (0, 0)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(6, 0), (4, 0), (2, 0), (0, 0)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
        elif input_pair == (6, 8):
            shift_combination = [[(4, 2), (2, 2), (0, 2), (0, 0)],
                                 [(4, 4), (2, 4), (0, 4), (2, 0)],
                                 [(4, 6), (2, 6), (0, 6), (4, 0)],
                                 [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
        elif input_pair == (6, 6):
            shift_combination = [[(2, 4), (0, 4), (0, 2), (0, 0)],
                                 [(4, 4), (4, 2), (2, 2), (2, 0)],
                                 [(-1, -1), (-1, -1), (-1, -1), (4, 0)],
                                 [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
        elif input_pair == (6, 4):
            if status == 'top_used':
                shift_combination = [[(-1, -1), (2, 2), (0, 2), (0, 0)],
                                    [(-1, -1), (4, 2), (4, 0), (2, 0)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (2, 2), (0, 2), (0, 0)],
                                     [(-1, -1), (4, 2), (4, 0), (2, 0)]]
        elif input_pair == (6, 2):
            if status == 'top_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (0, 0)],
                                    [(-1, -1), (-1, -1), (4, 0), (2, 0)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'top_used':
                shift_combination = [[(-1, -1), (0,0), (-1, -1), (-1, -1)],
                                     [(4, 0), (2, 0), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'bottom_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (0, 0)],
                                     [(-1, -1), (-1, -1), (4, 0), (2, 0)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (0, 0), (-1, -1), (-1, -1)],
                                     [(4, 0), (2, 0), (-1, -1), (-1, -1)]]
        elif input_pair == (4, 8):
            if status == 'top_used':
                shift_combination = [[(2, 4), (0, 4), (0, 2), (0, 0)],
                                     [(2, 6), (0, 6), (2, 2), (2, 0)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(2, 4), (0, 4), (0, 2), (0, 0)],
                                     [(2, 6), (0, 6), (2, 2), (2, 0)]]
        elif input_pair == (4, 6):
            if status == 'top_used':
                shift_combination = [[(-1, -1), (0, 4), (0, 2), (0, 0)],
                                    [(-1, -1), (2, 4), (2, 2), (2, 0)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (0, 4), (0, 2), (0, 0)],
                                     [(-1, -1), (2, 4), (2, 2), (2, 0)]]
        elif input_pair == (4, 4):
            if status == 'top_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (0, 2), (0, 0)],
                                    [(-1, -1), (-1, -1), (2, 2), (2, 0)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'top_used':
                shift_combination = [[(0, 2), (0, 0), (-1, -1), (-1, -1)],
                                     [(2, 2), (2, 0), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'bottom_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (0, 2), (0, 0)],
                                     [(-1, -1), (-1, -1), (2, 2), (2, 0)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(0, 2), (0, 0), (-1, -1), (-1, -1)],
                                     [(2, 2), (2, 0), (-1, -1), (-1, -1)]]
        elif input_pair == (4, 2):
            if status == 'top_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (0, 0)],
                                    [(-1, -1), (-1, -1), (-1, -1), (2, 0)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'top_used':
                shift_combination = [[(-1, -1), (0, 0), (-1, -1), (-1, -1)],
                                     [(-1, -1), (2, 0), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'bottom_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (0, 0)],
                                     [(-1, -1), (-1, -1), (-1, -1), (2, 0)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (0, 0), (-1, -1), (-1, -1)],
                                     [(-1, -1), (2, 0), (-1, -1), (-1, -1)]]
        elif input_pair == (2, 8):
            if status == 'top_used':
                shift_combination = [[(0, 6), (0, 4), (0, 2), (0, 0)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(0, 6), (0, 4), (0, 2), (0, 0)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
        elif input_pair == (2, 6):
            if status == 'top_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (0, 0)],
                                     [(-1, -1), (-1, -1), (0, 4), (0, 2)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'top_used':
                shift_combination = [[(-1, -1), (0, 0), (-1, -1), (-1, -1)],
                                     [(0, 4), (0, 2), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'bottom_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (0, 0)],
                                     [(-1, -1), (-1, -1), (0, 4), (0, 2)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (0, 0), (-1, -1), (-1, -1)],
                                     [(0, 4), (0, 2), (-1, -1), (-1, -1)]]
        elif input_pair == (2, 4):
            if status == 'top_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (0, 0)],
                                    [(-1, -1), (-1, -1), (-1, -1), (0, 2)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'top_used':
                shift_combination = [[(-1, -1), (0, 0), (-1, -1), (-1, -1)],
                                     [(-1, -1), (0, 2), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'bottom_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (0, 0)],
                                     [(-1, -1), (-1, -1), (-1, -1), (0, 2)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (0, 0), (-1, -1), (-1, -1)],
                                     [(-1, -1), (0, 2), (-1, -1), (-1, -1)]]
        elif input_pair == (2, 2):
            if status == 'top_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (0, 0)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                    [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'top_used':
                shift_combination = [[(-1, -1), (0, 0), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'bottom_right_used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (0, 0)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
            elif status == 'used':
                shift_combination = [[(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)],
                                     [(-1, -1), (0, 0), (-1, -1), (-1, -1)],
                                     [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]]
        else:
            assert 0 > 1, 'gen_opcode.py - unsupported quantization pair found'
        return shift_combination


    # when quantized to sub-byte levels, order of filling a bitBrick is
    # top-right -> top-left -> bottom-right -> bottom-left
    def assign_prod_to_fusionUnit(self, image_num, image_row_coor, image_col_coor, cycle, col, row, fu_name,
                                  kernel_num, kernel_row_coor, kernel_col_coor, inp, weight):
        # col and row are coordinates of the fusion unit
        # print("received image_num:{}, image_row_coor:{}, image_col_coor:{}, col:{}, row:{}".\
        #               format(image_num, image_row_coor, image_col_coor, col, row))
        # print("received kernel_num:{}, kernel_row_coor:{}, kernel_col_coor:{}, col:{}, row:{}".\
        #               format(kernel_num, kernel_row_coor, kernel_col_coor, col, row))

        input_loc = self.get_ibuf_address_for_coordinates(image_num, image_row_coor, image_col_coor, col, row)
        weight_loc = self.get_wbuf_address_for_coordinates(kernel_num, kernel_row_coor, kernel_col_coor, col, row)
        # print("input:{} is present at {} and weight:{} is present at {}".format(inp, input_loc, weight,weight_loc))

        cycle_name = "cycle"+str(cycle)
        col_name = 'col'+str(col)
        shift_combination = self.generate_bitBricks_usage_pattern(cycle_name, col_name, fu_name)
        for i in range(self.bitBrick_rows):
            for j in range(self.bitBrick_cols):
                bb_name = "BB_"+str(i)+"_"+str(j)

                if shift_combination[i][j] == (-1,-1):
                    continue
                else:
                    input_shift, weight_shift = shift_combination[i][j]
                command = fu_name+":"+bb_name+":mul2: "+hex(input_loc)+"-"+str(input_shift)+" "+hex(weight_loc)+"-"+str(weight_shift)
                # command = fu_name+":BB_"+str(i)+"_"+str(j)+":mul2: "+str(inp)+"-"+str(6 - 2*i)+" "+str(weight)+"-"+str(j*2)
                print("command:"+command)

                self.entire_sim_data[cycle_name][col_name][fu_name][bb_name]['command'] = command
                self.entire_sim_data[cycle_name][col_name][fu_name][bb_name]['status'] = 'used'


    def execGeneration(self):
        if len(self.input_image_shape) == 3:
            # multiple grayscale images
            for image in range(self.input_image_shape[0]):
                print("starting with image#{}".format(image))
                if (len(self.kernel_shape) == 3):
                    for kernel_num in range(self.kernel_shape[0]):
                        print("starting with kernel#{}".format(kernel_num))
                        self.execGeneration_for_each_image(image, self.input_image[image], self.input_image_shape[1:],
                                                            kernel_num, self.kernel[kernel_num], self.kernel_shape[1:])
                else:
                    print("starting with kernel#0")
                    self.execGeneration_for_each_image(image, self.input_image[image], self.input_image_shape[1:],
                                                       0, self.kernel, self.kernel_shape)
        elif len(self.input_image_shape) == 2:
            # single grayscale image
            print("starting with image#0")
            if len(self.kernel_shape) == 3:
                for kernel_num in range(self.kernel_shape[0]):
                    print("starting with kernel#{}".format(kernel_num))
                    self.execGeneration_for_each_image(0, self.input_image, self.input_image_shape,
                                                       kernel_num, self.kernel[kernel_num], self.kernel_shape[1:])
            else:
                print("starting with kernel#0")
                self.execGeneration_for_each_image(0, self.input_image, self.input_image_shape,
                                                   0, self.kernel, self.kernel_shape)
        else:
            assert 1 > 0, 'gen_opcode.py - execGeneration: unhandled case of input image shape'



    def execGeneration_for_each_image(self, image_num, input_single_image, input_single_image_shape, kernel_num, single_kernel, single_kernel_shape):
        # window_num = 0
        for r_i in range(input_single_image_shape[0] - single_kernel_shape[0] + 1):
            for c_i in range(input_single_image_shape[1] - single_kernel_shape[1] + 1):
                # starting of a window
                # all products inside a window would be spawned on a single column of FUs until fit
                # if not fit, spawn the remaining on next available column
                cycle_assigned, col_assigned = self.get_usable_bitfusion_col(self.window_num)

                prod_num = 0
                for r_w in range(single_kernel_shape[0]):
                    for c_w in range(single_kernel_shape[1]):
                        # starting of a kernel multiplication
                        product = input_single_image[r_i + r_w][c_i + c_w] * single_kernel[r_w][c_w]

                        cycle_assigned, col_assigned, row_assigned = self.get_usable_fusion_unit(col_assigned, self.window_num)
                        fu_assigned = 'FU_' + str(row_assigned) + "_" + str(col_assigned)
                        self.assign_prod_to_fusionUnit(image_num, r_i + r_w, c_i + c_w, cycle_assigned, col_assigned, row_assigned,\
                                                       fu_assigned, kernel_num, r_w, c_w, input_single_image[r_i + r_w][c_i + c_w], single_kernel[r_w][c_w])

                        print("window:{}, cycle:{}, FU:{}, {} * {}".format(self.window_num, cycle_assigned,\
                                                                                  fu_assigned, input_single_image[r_i + r_w][c_i + c_w], single_kernel[r_w][c_w]))
                        prod_num += 1

                self.window_num += 1
                # pprint(self.entire_mem_data)
                # if self.window_num == 4:
                #     exit(2)



if __name__ == "__main__":
    if os.path.exists("entire_sim_data.txt"):
        os.remove("entire_sim_data.txt")

    obuf_out_file_pattern = re.compile('^OBUF_x_(\d+).txt')

    for filename in os.listdir("./"):
        if obuf_out_file_pattern.match(filename):
            os.remove(filename)
    process = psutil.Process(os.getpid())
    print("memory taken by process in MB:{}".format(process.memory_info().rss/(1024*1024)))
    # single image
    input_image = [[1,2,3,4,5], [6,7,8,9,10], [11,12,13,14,15], [16,17,18,19,20], [21,22,23,24,25]]

    # multiple grayscale images
    # input_image = [[[1,2,3,4,5], [6,7,8,9,10], [11,12,13,14,15], [16,17,18,19,20], [21,22,23,24,25]],\
    #                [[26,27,28,29,30], [31,32,33,34,35], [36,37,38,39,40], [41,42,43,44,45], [46,47,48,49,50]],\
    #                [[51,52,53,54,55], [56,57,58,59,60], [61,62,63,64,65], [66,67,68,69,70], [71,72,73,74,75]]]

    input_image = np.array(input_image, dtype=int)

    # input_image = np.ones((10,28,28), dtype=int)
    # kernel = np.array([[151,152,153], [154,155,156], [157,158,159]])
    kernel = np.ones((1,4,4), dtype=int)

    padding = 0

    print("input_image_shape:{}".format(input_image.shape))

    if padding == 1:
        input_image = np.pad(input_image, (1, 1), 'constant', constant_values=(0))
        if len(input_image.shape) == 3:
            shape = input_image.shape
            input_image = input_image[1:(shape[0] - 1), :, :]
        elif len(input_image.shape) > 3:
            assert len(input_image.shape) <= 3, 'error! padding would not be correct'

    # print("input_image_shape:{}".format(input_image.shape))
    # print(input_image)
    # exit(2)

    GOp = gen_op_code(input_image, kernel, (4,4), (4,4), 256, 128, 256, 4, 6)
    GOp.add_new_cycle()
    #print(GOp.entire_sim_data)
    #print(json.dumps(GOp.entire_sim_data, indent=4))
    print(GOp.input_image)
    print(GOp.kernel)
    GOp.execGeneration()
    GOp.clear_cycle_from_sim_data('cycle'+str(GOp.cycles_used))

    # TODO next use data in dicts to generate instructions
    # TODO next display per cycle interesting stats - like how many BBs were free

    print(json.dumps(GOp.entire_sim_data, indent=4))
    pprint(GOp.entire_mem_data)
    print("cycles used:{}".format(GOp.cycles_used))

    print("memory taken by process in MB:{}".format(process.memory_info().rss/(1024*1024)))
