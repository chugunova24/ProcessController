import signal
import time
from typing import Callable


def timer(func: Callable):
    """
    Декоратор для вычисления времени выполнения произвольной функции.
    :param func: функция, время выполнения которой требуется вычислить
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()

        result = func(*args, **kwargs)

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"Execution time {func.__name__}: {execution_time} seconds")

        return result

    return wrapper


def timeout(*args):
    """
    Функция-посредник. Позволяет реализовать таймаут для запускаемых задач.
    Таймаут реализован с помощью сигнала.
    Из важных особенностей реализации можно выделить, что подобный подход
    доступен только в Unix/Linux системах.
    """
    setting = args[0]

    signal.setitimer(signal.ITIMER_REAL, setting.get("max_exec_time"), 0)

    func = setting.get("func")

    return func(*setting.get("args"))
