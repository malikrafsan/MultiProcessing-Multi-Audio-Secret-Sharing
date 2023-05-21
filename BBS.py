from MathUtils import MathUtils
import random
import math
import numpy as np

class BBS:
    def __init__(self, p: int, q: int, seed= None):
        if not self.__validate_p_q(p, q):
            raise Exception("p and q must be positive integers and congruent to 3 mod 4")

        self.p = p
        self.q = q
        self.n = p * q
        self.seed = self.__gen_seed(self.n, seed)

    def __validate_p_q(self, p: int, q: int):
        return ((p > 0 and q > 0) and 
                (p % 4 == 3 and q % 4 == 3) and 
                MathUtils.is_prime(p) and 
                MathUtils.is_prime(q))
    
    def __gen_seed(self, n: int, seed: int | None):
        seed = random.randint(2, n-1) if seed is None else seed
        while ((not MathUtils.coprime(n, seed)) and (not (seed >= 2 and seed < n))):
            seed = random.randint(2, n-1)
        
        return seed

    def gen_bits(self, num: int):
        bits = []
        for _ in range(num):
            self.seed = pow(self.seed, 2) % self.n
            # print(self.seed)
            bits.append(self.seed % 2)
        
        return bits

    def gen_bytes(self, num: int):
        bits = self.gen_bits(num * 8)
        return bytes([int("".join([str(bit) for bit in bits[i:i+8]]), 2) for i in range(0, len(bits), 8)])

    def randrange(self, lower_bound: int, upper_bound: int):
        num_bits = math.log2(upper_bound - lower_bound)
        bits = self.gen_bits(math.ceil(num_bits))
        # print(bits)
        num = int("".join([str(bit) for bit in bits]), 2)
        return num + lower_bound
