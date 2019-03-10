#!/usr/bin/python3

# import array
# import numpy as np

class shiftAdd():
    """Class to implement a shiftAdd"""
    def __init__(self, shiftAmts, inputs):
        """Constructor to initialize the shiftAmts and inputs"""
        print("shiftAdd.py<-__init__: inputs="+"self:"+str(self)+",")
        self.shiftAmts = shiftAmts
        self.inputs = inputs

    def computeSum(self, shiftAmts, inputs):
        """Returns the sum based on the inputs"""
        print("shiftAdd.py<-computeSum: inputs="+"self:"+str(self)+",")
        Sum = 0
        for shiftAmt in shiftAmts:
            index = shiftAmts.index(shiftAmt)
            Sum = Sum + (inputs[index] << shiftAmt)
        return Sum

    def printFinalSum_Latency(self):
        """Returns the final sum and latency for performing this operation"""
        print("shiftAdd.py<-printFinalSum: inputs="+"self:"+str(self)+",")
        FinalSum = self.computeSum(self.shiftAmts, self.inputs)
        return [FinalSum, 2.0]



SA0 = shiftAdd([0, 2, 2, 4], [2, 2, 4, 2])
print(SA0.printFinalSum_Latency())
