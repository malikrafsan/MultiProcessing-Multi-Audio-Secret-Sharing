class MathUtils:
    def coprime(a: int, b: int):
        while b != 0:
            a, b = b, a % b
        return a == 1

    def is_prime(n: int):
        if n == 2 or n == 3:
            return True
        if n < 2 or n % 2 == 0:
            return False
        if n < 9:
            return True
        if n % 3 == 0:
            return False

        r = int(n**0.5)
        f = 5
        while f <= r:
            if n % f == 0:
                return False
            if n % (f+2) == 0:
                return False
            f += 6
        return True
