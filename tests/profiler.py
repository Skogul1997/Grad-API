import cProfile


def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


cProfile.run("fib(35)")
