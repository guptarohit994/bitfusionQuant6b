#!/usr/bin/python3

# import array
# import numpy as np

class shiftAdd():
    """Class to implement a shiftAdd"""
    def __init__(self, name, input_objs, level=0):
        """Constructor to initialize the shiftAmts and inputs"""
        # print("shiftAdd.py <-__init__: inputs="+"self:"+str(self)+",")
        self.name = name
        # input_bb_obj = [[x,y],[a,b]] is the format
        assert type(input_objs) == list, 'shiftAdd - expecting input_bb_obj to be a list'
        self.inputObjs = input_objs
        self.outputs = []
        self.shiftAddLevel = level
        # self.outputObj = output_obj
        self.status = 'free'

    def execShiftAdd(self):
        assert len(self.inputObjs) == 2, 'shiftAdd - expecting inputBBobjs to be arranged as matrix'
        output  = (self.inputObjs[0][1].outputs.pop(0) << 0)
        output += (self.inputObjs[0][0].outputs.pop(0) << (2 + self.shiftAddLevel*2))
        output += (self.inputObjs[1][1].outputs.pop(0) << (2 + self.shiftAddLevel*2))
        output += (self.inputObjs[1][0].outputs.pop(0) << (4 + self.shiftAddLevel*4))
        self.outputs.append(output)
        self.status = 'complete'

    def computeSum(self, shiftAmts, inputs):
        """Returns the sum based on the inputs"""
        print("shiftAdd.py<-computeSum: inputs="+"self:"+str(self)+",")
        Sum = 0
        for shiftAmt in shiftAmts:
            index = shiftAmts.index(shiftAmt)
            Sum = Sum + (inputs[index] << shiftAmt)
        return Sum

    def displayAttributes(self):
        print("shiftAdd.py <- displayAttributes of {} at level: {}".format(self.name, self.shiftAddLevel))
        print("shiftAdd.py <- {} has status: {} and output: {}".format(self.name, self.status, self.outputs))


if __name__ == '__main__':
    SA0 = shiftAdd([0, 2, 2, 4], [2, 2, 4, 2], 0)
    print(SA0.printFinalSum_Latency())
    SA1 = shiftAdd([0, 4, 4, 8], [2, 2, 4, 2], 1)
    print(SA1.printFinalSum_Latency())
