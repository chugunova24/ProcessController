import time
from typing import Union


Number = Union[int, float]


class Functions:
    """
    Класс, содержащий методы, имитирующие бурную деятельность
    """

    @staticmethod
    def function0(f0_arg0: Number, f0_arg1: Number):
        print("Start function0")
        time.sleep(5)
        print("End function0")
        return f0_arg0 + f0_arg1

    @staticmethod
    def function1(f1_arg0: Number, f1_arg1: Number, f1_arg2: Number):
        print("Start function1")
        time.sleep(1)
        print("End function1")
        return f1_arg0 + f1_arg1 + f1_arg2

    @staticmethod
    def function2(arg0: Number):
        print("Start function2")
        time.sleep(2)
        print("End function2")
        return arg0
