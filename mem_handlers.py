import os
import utils
import numpy as np

class mem_handlers():
    def __init__(self):
        utils.cprint("mem_handlers", "__init__", "inputs=self:" + str(self))

    def create_mem(self, name, size):
        if os.path.exists(name):
            utils.cprint("mem_handlers", "create_mem", "memory file "+name+" exists. Will replace!")
            os.remove(name)

        buf_fd = open(name, 'w+b')
        buf_fd.seek(size - 1)
        buf_fd.write(b'\0')
        buf_fd.close()

    # reads size bytes from addr space of memory name
    def read_mem(self, name, addr, size):
        assert os.path.exists(name), 'memory file '+str(name)+' missing'

        buf_fd = open(name, 'r')
        buf_fd.seek(addr)
        data = []
        access_byte_cnt = 1
        while access_byte_cnt < (size+1):
            temp = buf_fd.read(1)

            temp = bytearray(temp, 'utf-8')
            data.append(int.from_bytes(temp, byteorder='little'))
            access_byte_cnt += 1
        data = np.array(data, dtype=np.int8)
        utils.cprint("mem_handlers", "read_mem", str(data))
        buf_fd.close()
        return data

    # stores data as list from starting address addr of memory name
    def write_mem(self, name, addr, data):
        assert os.path.exists(name), 'memory file ' + str(name) + ' missing'
        assert type(data) == list, 'write_mem expects data as list'

        buf_fd = open(name, 'rb+')
        buf_fd.seek(addr)
        buf_fd.write(bytes(data))
        buf_fd.close()


if __name__ == '__main__':
    mh = mem_handlers()
    mh.create_mem("rohit",0x8000)
    mh.write_mem("rohit", 0x400, [10, 11,12,13,14,15,16])
    mh.read_mem("rohit", 8, 32)
    mh.read_mem("rohit", 0x400, 16)