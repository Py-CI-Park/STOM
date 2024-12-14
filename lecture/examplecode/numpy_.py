import numpy as np

print(' 값이 0인 어레이 생성')
print(np.zeros(10))

print(' 값이 순차인 어레이 생성')
print(np.arange(10))

print(' 0~1까지 랜덤 어레이 생성')
print(np.random.rand(10))

print(' 값이 0인 2차원 어레이 생성')
print(np.zeros((5, 10)))

print(' 값이 0~1까지 2차원 랜덤 어레이 생성')
print(np.random.rand(5, 10))

print(' 1차원 어레이 합치기')
print(np.r_[np.zeros(10), np.arange(10)])

print(' 2차원 어레이 합치기1')
print(np.r_[np.zeros((5, 10)), np.random.rand(5, 10)])
# print(np.r_['0', np.zeros((5, 10)), np.random.rand(5, 10)])  # '0'은 생략 가능

print(' 2차원 어레이 합치기2')
print(np.r_['1', np.zeros((5, 10)), np.random.rand(5, 10)])

print(' 1차원 어레이 삭제')
print(np.delete(np.arange(10), 0))
print(np.delete(np.arange(10), -1))

print(' 2차원 어레이 마지막 로우 삭제')
print(np.delete(np.random.rand(5, 10), -1, 0))

print(' 2차원 어레이 마지막 칼럼 삭제')
print(np.delete(np.random.rand(5, 10), -1, 1))
