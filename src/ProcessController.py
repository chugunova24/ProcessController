import os
from queue import Queue
from typing import Optional

import multiprocessing
import threading

from utils import timer, timeout
from functions import Functions


class ProcessController:
    def __init__(self):
        # Максимальное кол-во одновременно выполняемых заданий
        self.max_n_processes = None
        # Очередь задач
        self.queue = Queue()
        # Список процессов
        self.processes = {}
        # Флаг, который определяет логический этап обработки всей очереди задач
        self.running = True

        # Мьютекс для очереди задач
        self._queue_lock = threading.Lock()
        # Переменная состояния для демона _launcher
        self._launcher_lock = threading.Condition()
        # Переменная состояния для _wait
        self._wait_lock = threading.Condition()
        # Переменная состояния для демона _waiter
        self._waiter_lock = threading.Condition()

        # демон _launcher
        self._launcher_thread = threading.Thread(target=self._launcher,
                                                 args=())
        self._launcher_thread.start()
        # демон _waiter
        self._waiter_thread = threading.Thread(target=self._waiter,
                                               args=())
        self._waiter_thread.start()

    def __del__(self) -> None:

        self.running = False
        with self._launcher_lock:
            self._launcher_lock.notify()
        for k in self.processes.keys():
            self.processes[k].kill()

        with self._wait_lock:
            self._wait_lock.notify()

        with self._waiter_lock:
            self._waiter_lock.notify()

    def _launcher(self) -> None:
        """
        Демон для запуска оставшихся в очереди задач, которые нельзя
        было запустить из-за ограничения максимального кол-ва
        одновременно выполняющихся процесов.
        Если очередь задач не пустая и кол-во текущих процесов меньше
        максимального кол-ва, то добавляем еще процессы.
        Посылает оповещения переменным состояния для функций waiter и wait.

        :return: None
        """

        while self.running:
            with self._launcher_lock:
                self._launcher_lock.wait_for(
                    lambda: (not self.queue.empty() and
                             len(self.processes) < self.max_n_processes
                             ) or not self.running)

            if not self.running:
                return
            with self._queue_lock:
                target = self.queue.get()
            p = multiprocessing.Process(target=timeout, args=(target,))
            p.start()
            self.processes[p.pid] = p

            with self._waiter_lock:
                self._waiter_lock.notify()

            with self._wait_lock:
                self._wait_lock.notify()

    def _waiter(self) -> None:
        """
        Демон, который ожидает, пока процесс завершится
        или обработка очереди задач закончится.
        Очищает список текущих процессов self.processes

        :return: None
        """
        while self.running:
            with self._waiter_lock:
                self._waiter_lock.wait_for(
                    lambda: (len(self.processes) > 0) or not self.running)

            if not self.running:
                return
            pid, status = os.wait()
            self.processes.pop(pid)
            with self._launcher_lock:
                self._launcher_lock.notify()
            with self._wait_lock:
                self._wait_lock.notify()

    def set_max_proc(self, n: int) -> int:
        """
        Метод устанавливает ограничение: максимальное число
        одновременно выполняемых заданий не должно превышать n.
        При этом обновляет информацию о max_n_processes для условия, которое
        использует launcher_lock (condition variable).

        :param n: новое значение максимального
        кол-ва одновременно выполняемых задач
        :return: обновленное значение максимального
        кол-ва одновременно выполняемых задач
        """
        self.max_n_processes = n
        with self._launcher_lock:
            self._launcher_lock.notify()

        return self.max_n_processes

    def start(self,
              max_exec_time: Optional[int] = None,
              tasks: Optional[list[tuple]] = None) -> None:
        """
        Данный метод помещает в очередь все задания из tasks. В случае,
        если не достигнуто ограничение на максимальное число одновременно
        работающих заданий, метод запускает выполнение заданий из очереди
        до тех пор, пока не будет достигнуто это ограничение.
        Запуск задания представляет порождение нового процесса, который
        выполняет соответствующую функцию с её аргументами. При этом каждый
        запущенный процесс для задания из tasks не должен работать дольше
        max_exec_time.

        :param max_exec_time: максимальное время (в секундах)
        работы каждого задания из списка tasks
        :param tasks: список заданий, содержащий
        информацию о функциях и аргументах функций.
        :return: None
        """
        if tasks and not max_exec_time:
            raise TypeError("start() missing "
                            "1 required positional argument: 'max_exec_time'")

        if not self.max_n_processes:
            raise TypeError("max_n_processes must"
                            " be int and greater than zero")

        # Заполнение очереди задач
        with self._queue_lock:
            if tasks:
                for task in tasks:
                    new_task = dict()
                    new_task["max_exec_time"] = max_exec_time
                    new_task["func"] = task[0]
                    new_task["args"] = task[1]
                    self.queue.put(new_task)

        # Отправка оповещения демону _launcher, который в свою очередь
        # будет добавлять новые задачи по мере освобождения списка процессов.
        with self._launcher_lock:
            self._launcher_lock.notify()

    def clean_processes(self) -> None:
        self.wait()
        self.processes = {}

        return

    @timer
    def wait(self) -> None:
        """
        Ожидание выполнения всех задач из очереди задач.

        :return: None
        """
        with self._wait_lock:
            self._wait_lock.wait_for(
                lambda: len(self.processes) == 0 and self.queue.empty())

        return

    def wait_count(self) -> int:
        """
        :return: Возвращает число заданий, которые осталось запустить.
        """
        return self.queue.qsize()

    def alive_count(self) -> int:
        """
        :return: Возвращает число выполняемых в данный момент заданий.
        """
        return [process.is_alive() for process in self.processes.values()
                ].count(True)


if __name__ == "__main__":
    # Пример выполнения

    # Экземпляр класса, содержащий методы, имитирующие бурную деятельность
    f = Functions()

    print("\n----First list----\n")

    # Первый список задач (6 задач)
    tasks = [
        (f.function0, (1, 1)),
        (f.function1, (1, 2, 3)),
        (f.function2, (1,)),
        (f.function0, (1, 1)),
        (f.function1, (1, 2, 3)),
        (f.function2, (1,))
    ]

    # Создаем экземпляр ProcessController
    controller = ProcessController()
    # По умолчанию set_max_proc = None, необходимо установить значение
    # max_n_processes. (6 задач одновременно)
    controller.set_max_proc(6)
    # Добавляем задачи в очередь задач и запускаем процессы.
    # Максимальное время выполнения 4 секунды.
    # Под условие max_exec_time НЕ попадает функция function0
    # (она засыпает на 5 секунд).
    # Функция function0 будет завершена досрочно.
    # То есть сообщение "End functionN" будет 4 раза
    # (function0 выполняется 2 раза).
    controller.start(tasks=tasks, max_exec_time=4)

    # Ожидание завершения процессов
    controller.wait()

    print("\n----Second list----\n")

    # Второй список задач (5 задач)
    tasks = [
        (f.function0, (1, 1)),
        (f.function1, (1, 2, 3)),
        (f.function2, (1,)),
        (f.function0, (1, 1)),
        (f.function1, (1, 2, 3)),
    ]

    # Устанавливаем максимальное кол-во задач (2 задачи одновременно)
    controller.set_max_proc(2)
    # Добавляем задачи в очередь задач и запускаем процессы.
    # Максимальное время выполнения 6 секунды.
    # Под условие max_exec_time попадают ВСЕ функции.
    # То есть сообщений "End functionN" будет 5 раз
    controller.start(tasks=tasks, max_exec_time=6)

    # Ожидание завершения процессов
    controller.wait()

    controller.__del__()
