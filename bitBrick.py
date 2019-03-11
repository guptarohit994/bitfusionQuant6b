#!/usr/bin/python3
# import array
import numpy as np
import constants as constants

class bitBrick():
    """ Class to implement a BitBrick """
    def __init__(self, name):
        print("BitBrick.py<-__init__: inputs="+"self:"+str(self)+","+"name:"+str(name)+",")
        self.name = name
        self.input_A = 0
        self.input_B = 0
        self.status = "free"
        self.latency = constants.latency_bitbrick
        self.product = 0
        print("The name and value are {} and {}, {}".format(self.name,self.input_A, self.input_B))

    def displayAttributes(self):
        """ Function to print the attributes of an object of BitBrick class"""
        print("BitBrick.py<-displayAttributes: inputs="+"self:"+str(self)+",")
        print("The name of the object is {}".format(self.name))
        print("The inputs to the bitbrick are {} and {}".format(self.input_A, self.input_B))

    def computeProduct(self):
        """ Function returns the product computed after multiplication of multiplier and multiplicand"""
        print("BitBrick.py<-computeProduct: inputs="+"self:"+str(self)+",")
        product = self.input_A * self.input_B
        self.product = product

    def assignInputs(self, input_A, input_B):
        print("bitBrick.py<-assignInputs")
        if self.status != "busy":
            self.input_A = input_A
            self.input_B = input_B
            self.status = "busy"
            assert abs(self.input_A) <= 3, 'bitBrick error - input greater than 2 bits'
            assert abs(self.input_B) <= 3, 'bitBrick error - input greater than 2 bits'
        return self.status

    def getProductLatency(self):
        """ Returns the product and latency """
        print("BitBrick.py<-printProduct_Latency: inputs="+"self:"+str(self)+",")
        return self.product, self.latency


if __name__ == "__main__":
    BB0 = bitBrick('BB0')
    BB0.assignInputs(-2, 2)
    BB0.computeProduct()
    print(BB0)

    BB0.displayAttributes()

    Prod_Latency = BB0.getProductLatency()
    print(Prod_Latency)
