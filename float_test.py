import numpy as np


def reg_to_float(data_list):
    data_int = ((data_list[1] << 16) & 0xFFFF0000) + (data_list[0] & 0xFFFF)
    sign = (data_int >> 31) & 0x1
    exp = ((data_int >> 23) & 0xFF) - 127
    man = 1 + ((data_int & 0x7FFFFF) / 0x7FFFFF)
    # print("sign = {:d}, exp = {:d}, man = {:.3E}, val = {:.6E}".format(sign, exp, man, (1**(sign-1))*man*(2**exp)))
    data_float = np.float32(data_int)
    return data_float


if __name__ == "__main__":
    data = [0xA770, 0x41A5]
    print(reg_to_float(data))