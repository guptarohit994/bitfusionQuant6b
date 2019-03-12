def cprint(file, func, message):
    print(str(file)+" <- "+str(func)+" "+str(message))

def bindigits(n, bits):
    s = bin(n & int("1"*bits, 2))[2:]
    return ("{0:0>%s}" % (bits)).format(s)

def getNameString(unit, row, col):
    return unit+"_"+str(row)+"_"+str(col)