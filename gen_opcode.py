import numpy as np
from memory import *
import json
import os
import psutil


class gen_op_code():
    # bitfusion_dim is a tuple indicating how many rows and columns in bitfusiont
    def __init__(self, input_image, kernel, bitfusion_dim=(4,4), bitbrick_dim=(4,4)):
        self.input_image = input_image
        self.kernel = kernel
        self.entire_sim_data = {}
        self.cycles_used = 0
        self.input_image_shape = self.input_image.shape
        self.kernel_shape = self.kernel.shape
        # tells how many fusionUnits inside bitFusion
        self.bitFusion_rows = bitfusion_dim[0]
        self.bitFusion_cols = bitfusion_dim[1]
        # tells how many bitBricks inside a fusionUnit
        self.bitBrick_rows = bitbrick_dim[0]
        self.bitBrick_cols = bitbrick_dim[1]

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





    def get_next_bitBrick_in_fusionUnit(self):
        temp = 1

    def add_new_cycle(self):
        self.cycles_used += 1
        self.init_cycle_in_db(self.cycles_used)

    def get_usable_bitfusion_col(self, window_num):
        cur_cycle = self.cycles_used

        for colNum in range(self.bitFusion_cols):
            if self.entire_sim_data['cycle'+str(cur_cycle)]['col'+str(colNum)]['status'] == 'free':
                self.entire_sim_data['cycle' + str(cur_cycle)]['col' + str(colNum)]['status'] = 'used'
                print("gen_opcode.py <- get_usable_bitfusion_col= window:{} can be accomodated in cycle:{} at col:{}".\
                      format(window_num, self.cycles_used, colNum))
                return cur_cycle, colNum

        # if reached here, it means next cycle needed
        self.add_new_cycle()
        cur_cycle = self.cycles_used
        for colNum in range(self.bitFusion_cols):
            if self.entire_sim_data['cycle'+str(cur_cycle)]['col'+str(colNum)]['status'] == 'free':
                self.entire_sim_data['cycle' + str(cur_cycle)]['col' + str(colNum)]['status'] = 'used'
                print("gen_opcode.py <- get_usable_bitfusion_col= window:{} can be accomodated in cycle:{} at col:{}".\
                      format(window_num, self.cycles_used, colNum))
                return cur_cycle, colNum

    def get_usable_fusion_unit(self, col, window_num):
        cur_cycle = self.cycles_used

        for rowNum in range(self.bitFusion_rows):
            if self.entire_sim_data['cycle'+str(cur_cycle)]['col'+str(col)]['FU_'+str(rowNum)+"_"+str(col)]['status'] == 'free':
                self.entire_sim_data['cycle'+str(cur_cycle)]['col'+str(col)]['FU_'+str(rowNum)+"_"+ str(col)]['status'] = 'used'
                return cur_cycle, col, rowNum

        # if reached here, it means next column is needed
        cur_cycle, newCol = self.get_usable_bitfusion_col(window_num)
        for rowNum in range(self.bitFusion_rows):
            if self.entire_sim_data['cycle'+str(cur_cycle)]['col'+str(newCol)]['FU_'+str(rowNum)+"_"+str(newCol)]['status'] == 'free':
                self.entire_sim_data['cycle'+str(cur_cycle)]['col'+str(newCol)]['FU_'+str(rowNum)+"_"+str(newCol)]['status'] = 'used'
                return cur_cycle, newCol, rowNum

    def assign_prod_to_fusionUnit(self, cycle, col, row, fu_name, inpA, inpB):
        for i in range(self.bitBrick_rows):
            for j in range(self.bitBrick_cols):
                # TODO change to memory locations
                command = fu_name+":BB_"+str(i)+"_"+str(j)+":mul2: "+str(inpA)+"-"+str(6 - 2*i)+" "+str(inpB)+"-"+str(j*2)
                self.entire_sim_data['cycle'+str(cycle)]['col'+str(col)]['FU_'+str(row)+"_"+str(col)]['BB_'+str(i)+"_"+str(j)]\
                    ['command'] = command
                self.entire_sim_data['cycle'+str(cycle)]['col'+str(col)]['FU_'+str(row)+"_"+str(col)]['BB_'+str(i)+"_"+str(j)] \
                    ['status'] = 'used'

    def execGeneration(self):
        window_num = 0
        for r_i in range(self.input_image_shape[0] - self.kernel_shape[0] + 1):
            for c_i in range(self.input_image_shape[1] - self.kernel_shape[1] + 1):
                # starting of a window
                # all products inside a window would be spawned on a single column of FUs until fit
                # if not fit, spawn the remaining on next available column
                cycle_assigned, col_assigned = self.get_usable_bitfusion_col(window_num)

                prod_num = 0
                for r_w in range(self.kernel_shape[0]):
                    for c_w in range(self.kernel_shape[1]):
                        # starting of a kernel multiplication
                        product = self.input_image[r_i + r_w][c_i + c_w] * self.kernel[r_w][c_w]

                        cycle_assigned, col_assigned, row_assigned = self.get_usable_fusion_unit(col_assigned, window_num)
                        fu_assigned = 'FU_' + str(row_assigned) + "_" + str(col_assigned)
                        self.assign_prod_to_fusionUnit(cycle_assigned, col_assigned, row_assigned,\
                                                       fu_assigned,self.input_image[r_i + r_w][c_i + c_w], self.kernel[r_w][c_w])

                        print("window:{}, cycle:{}, FU:{}, {} * {}".format(window_num, cycle_assigned,\
                                                                                  fu_assigned, self.input_image[r_i + r_w][c_i + c_w], self.kernel[r_w][c_w]))
                        prod_num += 1
                window_num += 1



if __name__ == "__main__":
    # process = psutil.Process(os.getpid())
    # print("memory taken by process in MB:{}".format(process.memory_info().rss/(1024*1024)))
    input_image = [[1,2,3,4,5], [6,7,8,9,10], [11,12,13,14,15], [16,17,18,19,20], [21,22,23,24,25]]
    input_image = np.array(input_image, dtype=int)
    kernel = np.array([[51,52,53], [54,55,56], [57,58,49]])

    GOp = gen_op_code(input_image, kernel, (4,4), (4,4))
    GOp.add_new_cycle()
    #print(GOp.entire_sim_data)
    #print(json.dumps(GOp.entire_sim_data, indent=4))
    print(GOp.input_image)
    print(GOp.kernel)
    GOp.execGeneration()
    #print(json.dumps(GOp.entire_sim_data, indent=4))
    print("cycles used:{}".format(GOp.cycles_used))
    # print("memory taken by process in MB:{}".format(process.memory_info().rss/(1024*1024)))
    '''
# input_image = [[1,0,0,2,2],[0,2,0,1,2],[0,0,2,2,2],[1,1,2,1,1],[0,0,0,2,0]]
input_image = [[1,2,3,4,5], [6,7,8,9,10], [11,12,13,14,15], [16,17,18,19,20], [21,22,23,24,25]]
input_image = np.array(input_image, dtype=int)
entire_sim_data = {}
cycles_used = 0


padding = 1

print(input_image.shape)

if padding == 1:
    input_image = np.pad(input_image, (1,1), 'constant', constant_values=(0))
    if len(input_image.shape) == 3:
        shape = input_image.shape
        input_image = input_image[1:(shape[2]-1),:,:]
    elif len(input_image.shape) > 3:
        assert len(input_image.shape) <= 3, 'error! padding would not be correct'

print(input_image)

kernel_1 = np.array([[51,52,53], [54,55,56], [57,58,49]])
print(kernel_1)

input_image_shape = input_image.shape
kernel_1_shape = kernel_1.shape
output_img = np.zeros((input_image_shape[0]-kernel_1_shape[0]+1, input_image_shape[1]-kernel_1_shape[1]+1))

window_col_start = 0
window_col_end = 0
window_row_start = 0
window_row_end = 0

count = 0
window = 0
# contains data that should be present in ibuf of each bb
input_image_window_data = []

instr_file = open("instr.txt", "w")

def gen_bitBrick_code():
    temp = 1

def get_next_fusion_unit():
    temp = 1

def get_next_bitfusion_column():
    temp = 1





# window moves --> and then down and the again -->
for r in range(input_image_shape[0]-kernel_1_shape[0]+1):
    for c in range(input_image_shape[1]-kernel_1_shape[1]+1):
        input_image_window_data.append([])
        window_product_num = 0
        for x in range(kernel_1_shape[0]):
            for y in range(kernel_1_shape[1]):
                ibuf = memory("IBUF_"+str(window_product_num)+"_"+str(window), 1024)
                wbuf = memory("WBUF_"+str(window_product_num)+"_"+str(window), 1024)
                count += 1
                product = str(input_image[r+x, c+y]) + " * " + str(kernel_1[x, y])
                input_image_window_data[window].append(input_image[r+x, c+y])
                print("FU_{}_{}:mul2 {} {} = {}".\
                      format(window_product_num, window,\
                             input_image[r+x, c+y], kernel_1[x, y], input_image[r+x, c+y] * kernel_1[x, y]))
                for i in range(4):
                    for j in range(4):
                        instr_file.write("FU_{}_{}:BB_{}_{}:mul2 0x{}-{} 0x{}-{}\n".\
                                 format(window_product_num, window, i, j, \
                                        0, (6 - (2 * i)), \
                                        0, j*2))
                # print("count:{}, window:{}, {}".format(count, window, product))
                print("write to IBUF_{}_{} <- {}".format(window_product_num, window, [input_image_window_data[window][window_product_num]]))
                ibuf.store_mem(0x0, [input_image_window_data[window][window_product_num]])
                print("write to WBUF_{}_{} <- {}".format(window_product_num, window, [kernel_1.reshape(9).tolist()[window_product_num]]))
                wbuf.store_mem(0x0, [kernel_1.reshape(9).tolist()[window_product_num]])
                window_product_num += 1
        window += 1

print(input_image_window_data)
instr_file.close()
'''
