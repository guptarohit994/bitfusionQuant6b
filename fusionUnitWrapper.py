from bitBrick import *
from memory import *
from fusionUnit import *
import utils as utils
from shiftAdd import *

class fusionUnitWrapper():
    def __init__(self):
        # TODO decide how many fusion unit should be there in a row
        self.fuRows = 16
        self.fuCols = 16

        self.fuData = {}
        self.obuf_list = []
        self.commands = []
        # stores objs of fu in a column
        self.col_fu_obj = [[0 for x in range(self.fuRows)] for y in range(self.fuCols)]
        # stores objs of adders of each column
        self.shiftAdd_l2_objs = []

        for i in range(self.fuRows):
            for j in range(self.fuCols):
                fu_name = "FU_"+str(i)+"_"+str(j)
                fu_wbuf_name = 'WBUF_'+str(i)+"_"+str(j)
                fu_ibuf_name = 'IBUF_'+str(i)+"_"+str(j)

                fu_ibuf_obj = memory(fu_ibuf_name, 1024)
                fu_wbuf_obj = memory(fu_wbuf_name, 1024)
                fu_obj = fusionUnit(fu_name, fu_ibuf_name, fu_ibuf_obj,\
                                    fu_wbuf_name, fu_wbuf_obj, 2)

                self.fuData[fu_name] = {}
                self.fuData[fu_name]['fu_obj'] = fu_obj
                self.fuData[fu_name]['fu_ibuf_obj'] = fu_ibuf_obj
                self.fuData[fu_name]['fu_wbuf_obj'] = fu_wbuf_obj


        for j in range(self.fuCols):
            for i in range(self.fuRows):
                self.col_fu_obj[j][i] = self.fuData[utils.getNameString('FU',i, j)]['fu_obj']

        for j in range(self.fuCols):
            col_sa_obj = shiftAdd('SA_x_'+str(j), self.col_fu_obj[j], 'BitFusion', 2)
            self.shiftAdd_l2_objs.append(col_sa_obj)

            obuf_name = 'OBUF_x_'+str(j)
            obuf_obj = memory(obuf_name, 1024)
            self.obuf_list.append(obuf_obj)

    # FU_0_1:BB_0_1:mul2 0x400-0 0x420-0
    def parseCommand(self, command):
        print(command)
        command_blocks = command.split(':')
        assert len(command_blocks) == 3, 'fusionUnitWrapper - malformed command received'
        command_blocks[1] += ":"+command_blocks.pop(2)
        pattern = re.compile('^FU_(\d+)_(\d+)$')
        matches = pattern.match(command_blocks[0])
        assert matches, 'fusionUnitWrapper - malformed target FF name received'

        # return [<BB row num> <BB col num> <op> <memLoc of operand1> <memLoc of operand2>]
        return [matches.group(1), matches.group(2)] + command_blocks[1:]

    def addCommand(self, command):
        if type(command) == list:
            self.commands += command
        else:
            self.commands.append(command)

    def sendCommand(self):
        while len(self.commands) != 0:
            command_blocks = self.parseCommand(self.commands.pop(0))
            fu_row = command_blocks[0]
            fu_col = command_blocks[1]
            fu_command = command_blocks[2]

            self.fuData[utils.getNameString('FU',fu_row,fu_col)]['fu_obj'].addCommand(fu_command)

        for i in range(self.fuRows):
            for j in range(self.fuCols):
                self.fuData[utils.getNameString('FU', i, j)]['fu_obj'].sendCommand()

    def execCommand(self):
        for i in range(self.fuRows):
            for j in range(self.fuCols):
                self.fuData[utils.getNameString('FU',i,j)]['fu_obj'].execCommand()

        for j in range(self.fuCols):
            self.shiftAdd_l2_objs[j].execAdd()
            self.shiftAdd_l2_objs[j].displayAttributes()



    def getBusyBitBricks(self):
        for i in range(self.fuRows):
            for j in range(self.fuCols):
                self.fuData[utils.getNameString('FU',i,j)]['fu_obj'].getBusyBitBricks()

if __name__ == "__main__":
    DD = fusionUnitWrapper()
    with open('instr.txt') as f:
        command = f.read().splitlines()
    # command = ["FU_0_0:BB_1_1:mul2 0x0-4 0x0-2", "FU_15_1:BB_1_1:mul2 0x0-4 0x0-2"]
    # DD.fuData[utils.getNameString('FU',0,0)]['fu_ibuf_obj'].store_mem(0x0, [231,1,1,1,1,1,1,1])
    # DD.fuData[utils.getNameString('FU',0,0)]['fu_wbuf_obj'].store_mem(0x0, [165,1,2,3,4,5,6,7])
    # DD.fuData[utils.getNameString('FU',15,1)]['fu_ibuf_obj'].store_mem(0x0, [231,1,1,1,1,1,1,1])
    # DD.fuData[utils.getNameString('FU',15,1)]['fu_wbuf_obj'].store_mem(0x0, [165,1,2,3,4,5,6,7])
    DD.addCommand(command)
    DD.sendCommand()
    DD.getBusyBitBricks()
    DD.execCommand()




