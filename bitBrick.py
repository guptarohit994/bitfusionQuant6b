#!/usr/bin/python3
# import array
# import numpy as np

class bitBrick():
    """ Class to implement a BitBrick """
    def __init__(self, name, inputs, ID):
        print("BitBrick.py<-__init__: inputs="+"self:"+str(self)+","+"name:"+str(name)+",")
        self.name = name
        self.input_A = inputs[0]
        self.input_B = inputs[1]
        self.ID = ID

    def displayAttributes(self):
        """ Function to print the attributes of an object of BitBrick class"""
        print("BitBrick.py<-displayAttributes: inputs="+"self:"+str(self)+",")
        print("The name and the ID of the object is {}".format(self.name, self.ID))
        print("The inputs to the bitbrick are {} and {}".format(self.input_A, self.input_B))

    def computeProduct(self, multiplier, multiplicand):
        """ Function returns the product computed after multiplication of multiplier and multiplicand"""
        print("BitBrick.py<-computeProduct: inputs="+"self:"+str(self)+",")
        product = multiplier*multiplicand
        returnVal = [product, 2.0]
        return returnVal

    def printProduct_Latency(self):
        """ Returns the product and latency """
        print("BitBrick.py<-printProduct_Latency: inputs="+"self:"+str(self)+",")
        if (self.input_A < 0):
            rightShiftA = self.input_A >> 3
            if (rightShiftA == -1):
                rightShiftA = 0
        else:
            rightShiftA = self.input_A >> 3
        
        if (self.input_B < 0):
            rightShiftB = self.input_B >> 3
            if (rightShiftB == -1):
                rightShiftB = 0
        else:
            rightShiftB = self.input_B >> 3

        assert (not(rightShiftA) and not(rightShiftB)), 'Values are greater than 3 bits'
        Product_Latency = self.computeProduct(self.input_A, self.input_B)
        return Product_Latency[0], Product_Latency[1]

if __name__== "__main__":
    BB0 = bitBrick('BB0', [-4, 2], "0_0_0")
    print(BB0)

    BB0.displayAttributes()

    Prod_Latency = BB0.printProduct_Latency()
    print(Prod_Latency)
