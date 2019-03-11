#!/usr/bin/python3

import bitBrick
import shiftAdd

class fusionUnit(bitBrick.bitBrick, shiftAdd.shiftAdd):
    """Class for representing the fusionUnit"""
    def __init__(self, name, input_pixel, weight, \
            input_pixel_resolution, weight_resolution \
            ID, BB_countX, BB_countY):
        """ Constructor class for the Fusion Unit """
        self.name = name
        self.input_pixel = input_pixel
        self.weight = weight
        self.input_pixel_resolution = input_pixel_resolution
        self.weight_resolution = weight_resolution
        self.ID = ID
        self.rows = BB_countY
        self.cols = BB_countX
        self.BB_list = [][] # Used to store the BB objects
        for i in range(self.rows):
            for j in range(self.cols):
                BB_name = "BB_"+str(i)+"_"+str(j)
                self.BB_list[i][j] = bitBrick.bitBrick(BB_name)

    def scheduleProduct(self, inputPixel, inputWeight):
        # Compute the number of BBs required
    
    def computeBBreqd(self):


    def getfreeBBCount(self):
        count = 0
        for i in range(self.rows):
            for j in range(self.cols):
                if self.BB_list[i][j].status != "busy":
                    count = count + 1
        return count



        # BBx is being initialized to 0
        self.A0 = (self.input_pixel & 3)
        self.A1 = (self.input_pixel & (3 << 2)) >> 2
        self.A2 = (self.input_pixel & (3 << 4)) >> 4
        self.A3 = (self.input_pixel & (3 << 6)) >> 6

        self.B0 = (self.weight & 3)
        self.B1 = (self.weight & (3 << 2)) >> 2
        self.B2 = (self.weight & (3 << 4)) >> 4
        self.B3 = (self.weight & (3 << 6)) >> 6
        
        # Computing these values
        self.BB0  = bitBrick.bitBrick('BB0',[self.A0, self.B0], "0_0")
        # super(fusionUnit, self).__init__('BB0', [self.A0, self.B0], "0_0")
        self.BB1  = bitBrick.bitBrick('BB1',[self.A0, self.B1], "0_1")
        self.BB2  = bitBrick.bitBrick('BB2',[self.A1, self.B0], "0_2")
        self.BB3  = bitBrick.bitBrick('BB3',[self.A1, self.B1], "0_3")
        self.BB4  = bitBrick.bitBrick('BB4',[self.A0, self.B2], "1_0")
        self.BB5  = bitBrick.bitBrick('BB5',[self.A1, self.B2], "1_1")
        self.BB6  = bitBrick.bitBrick('BB6',[self.A0, self.B3], "1_2")
        self.BB7  = bitBrick.bitBrick('BB7',[self.A1, self.B3], "1_3")
        self.BB8  = bitBrick.bitBrick('BB8',[self.A2, self.B0], "2_0")
        self.BB9  = bitBrick.bitBrick('BB9',[self.A2, self.B1], "2_1")
        self.BB10  = bitBrick.bitBrick('BB10',[self.A3, self.B0], "2_2")
        self.BB11  = bitBrick.bitBrick('BB11',[self.A3, self.B1], "2_3")
        self.BB12  = bitBrick.bitBrick('BB12',[self.A2, self.B2], "3_0")
        self.BB13  = bitBrick.bitBrick('BB13',[self.A2, self.B3], "3_1")
        self.BB14  = bitBrick.bitBrick('BB14',[self.A3, self.B2], "3_2")
        self.BB15  = bitBrick.bitBrick('BB15',[self.A3, self.B3], "3_3")
        #
    def displayAttributes(self):
        print("fusionUnit.py<-displayAttributes: inputs="+"self:"+str(self))
        print("The input pixel's value is {}".format(self.input_pixel))
        print("The input weight's value is {}".format(self.weight))
        print("The input pixel's resolution is {}".format(self.input_pixel_resolution))
        print("The input weight's resolution is {}".format(self.weight_resolution))

    def computeProdLatency(self):
        """Returns the final product and the latency of the operation"""
        # Compute the intermediate products
        self.product00 = self.BB0.printProduct
        self.intermProd0 = shiftAdd([0,2,2,4],[self.BB0,self.BB1,self.BB2,self.BB3], 0)



if __name__=="__main__":
    FF0 = fusionUnit('FF0', 127, -1, 8, 8, "0_0")
    FF0.computeProdLatency()
