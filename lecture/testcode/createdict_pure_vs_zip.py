import time
import numpy as np


data_list1 = list(np.random.rand(1000000))
data_list2 = list(np.random.rand(1000000))

dict_test = {}
start = time.time()
for i in range(len(data_list1)):
    dict_test[data_list1[i]] = data_list2[i]
print(time.time() - start)

start = time.time()
dict_test = dict(zip(data_list1, data_list2))
print(time.time() - start)
