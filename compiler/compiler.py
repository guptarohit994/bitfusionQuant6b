#!/usr/bin/python3

import re
# import constants

# Check the .py file for the first layer and extract the following information
#   1. Input image dimensions (M x N)
#   2. Number of filters (C)
#   3. Kernel Size
#   4. Activation type
#   5. Whether pooling is being done? If yes, what type of pooling - max, average

inputFile = open("keras_implementation.py", "r")
# print(inputFile.read())

# Printing the contents of the line!

# Computing the patterns from the Keras code!
count_pattern1 = 0
count_pattern2 = 0
count_pattern3 = 0
count_pattern4 = 0
count_pattern5 = 0

pattern1 = "layers"
pattern2 = "Conv2D"
pattern3 = "AveragePooling"
pattern4 = "Flatten"
pattern5 = "Dense"
pattern6 = "poolingtype"

# Now that we have computed the different types of layers, 
# let's compute the image dimensions, kernel size and activations

kernelSize_pattern = "kernel_size"
pooling_pattern = "Pooling2D"
filterCount_pattern = "filters"
activation_pattern = "activation"
inputShape_pattern = "input_shape"

kernelSize_values = []
filterCount_values = []
activation_values = []
inputShape_values = []
poolingType_values = []

found_kernelSize = False
found_filterCount = False
found_activation = False
found_inputShape = False
found_poolingType = False

# Extract kernelSize information for all the layers
for line in open("keras_implementation.py", "r"):
    if not found_kernelSize:
        counter_kernelSize = 0
        if re.search(kernelSize_pattern, line):
            for part in line.split('( | )'):
                counter_kernelSize += 1
                if kernelSize_pattern in part:
                    # We will need two values
                    kernelSize_values.append(line.split()[counter_kernelSize])
                    kernelSize_values.append(line.split()[counter_kernelSize + 1])

found_kernelSize = True
print(kernelSize_values)

kernelSize_val = ""
for value in kernelSize_values:
    kernelSize_val += str(value)

# How do I extract (3,3) from the kernelSize_val variable?

# Extract filterCount information for all the layers
for line in open("keras_implementation.py", "r"):
    if not found_filterCount:
        counter_filter = 0
        if re.search(filterCount_pattern, line):
            for part in line.split('='):
                if filterCount_pattern in part:
                    filterCount_values.append(line.split()[counter_filter])

found_filterCount = True
print(filterCount_values)

# Extract activation information for all the layers
for line in open("keras_implementation.py", "r"):
    if not found_activation:
        counter_activation = 0
        if re.search(activation_pattern, line):
            for part in line.split('='):
                if activation_pattern in part:
                    index = line.split('=').index(part)
                    activation_values.append(line.split('=')[index+1])

found_activation = True
print(activation_values)

# Extract the input dimensions of the image that needs to be used -
for line in open("keras_implementation.py", "r"):
    if not found_inputShape:
        counter_inputShape = 0
        if re.search(inputShape_pattern, line):
            for part in line.split('='):
                if inputShape_pattern in part:
                    index = line.split('=').index(part)
                    inputShape_values.append(line.split('=')[index+1])

found_inputShape = True
print(inputShape_values)

# Extract the type of pooling that's happening in the layers
for line in open("keras_implementation.py", "r"):
    if not found_poolingType:
        if re.search(pooling_pattern, line):
            poolingType_values.append(line.split('.')[-1])

found_poolingType = True
print(poolingType_values)
