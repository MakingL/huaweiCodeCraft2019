# -*- coding: utf-8 -*-
# @Time    : 2019/3/28 22:43
# @Author  : MLee
# @File    : AdjustArg.py
import logging
import time

from Simulator.Simulator import CheckAnswer
from solution.getSolution import GetSolution


class AdjustArg(object):
    """
        调参的类
        用于参数的自动搜索
    """

    def __init__(self, conf, argument_dict, arg_save_path="./arg_info.txt"):
        super(AdjustArg, self).__init__()
        self.conf = conf

        self.const = argument_dict.get("const", [])
        self.omega = argument_dict.get("omega", [])
        self.alpha = argument_dict.get("alpha", [])
        self.gama = argument_dict.get("gama", [])
        self.a = argument_dict.get("a", [])
        self.b = argument_dict.get("b", [])
        self.c = argument_dict.get("c", [])

        self.alpha_best = 0
        self.gama_best = 0
        self.omega_best = 0
        self.const_best = 0
        self.a_best = 0
        self.b_best = 0
        self.c_best = 0

        self.arg_save_path = arg_save_path

    def start_adjust_arg(self):
        """
        自动搜索参数，即传入参数，看指定参数下的输出结果，保存最优的参数值
        :return:
        """
        search_epoch = 0
        last_progress = 0

        time_min = float("inf")

        total_epoch = len(self.alpha) * len(self.a) * len(self.b) * len(self.c) * len(self.gama) * len(self.const)
        print("Start search argument...")
        for alpha in self.alpha:
            for gama in self.gama:
                for a in self.a:
                    for b in self.b:
                        for c in self.c:
                            for const in self.const:
                                # for omega in self.omega:

                                omega = None
                                # ******* 显示搜索进度信息 **********
                                search_epoch += 1
                                search_progress = search_epoch / total_epoch * 100
                                if search_progress - last_progress >= 5:
                                    last_progress = search_progress
                                    print("Argument search progress: {}%".format(search_progress))

                                # ****** 获得结果 **********
                                solution = GetSolution(self.conf)
                                solution.set_argument(omega=omega, alpha=alpha, gama=gama, const_data=const,
                                                      batch_a=a, batch_b=b, batch_c=c)
                                solution.load_data_and_build_graph()
                                time_slice = solution.compute_result()
                                if time_slice < 0:
                                    # 有负权值边
                                    continue
                                solution.output_solution()

                                # ******* 判题器模拟 *********
                                # 记录判题器调度时间
                                start_time = time.clock()

                                car_path, road_path, cross_path, answer_path = self.conf
                                simulator = CheckAnswer(car_path, road_path, cross_path, answer_path)
                                simulate_result = simulator.simulating()
                                if simulate_result < 0:
                                    # 死锁
                                    continue

                                end_time = time.clock()
                                # 获得调度时间
                                time_cost = end_time - start_time

                                if time_cost < time_min:
                                    time_min = time_cost
                                    self.alpha_best = alpha
                                    self.gama_best = gama
                                    self.omega_best = omega
                                    self.const_best = const
                                    self.a_best = a
                                    self.b_best = b
                                    self.c_best = c
                                    logging.info("Get a better time cost: {}, alpha: {} gama: {},"
                                                 " omega: {}, const: {}, a: {}, b: {}, c: {}\n".format(time_min,
                                                                                                       self.alpha_best,
                                                                                                       self.gama_best,
                                                                                                       self.omega_best,
                                                                                                       self.const_best,
                                                                                                       self.a_best,
                                                                                                       self.b_best,
                                                                                                       self.c_best))
                                arg_dict = dict()
                                arg_dict["omega"] = omega
                                arg_dict["const"] = const
                                arg_dict["alpha"] = alpha
                                arg_dict["gama"] = gama
                                arg_dict["time_cost"] = time_cost
                                arg_dict["a"] = a
                                arg_dict["b"] = b
                                arg_dict["c"] = c

                                # 保存当前参数结果
                                self.save_search_result(arg_dict, False)

        # 参数搜索结束
        logging.info("Argument search Done")
        logging.info("Best time cost: {}, alpha: {} gama: {},"
                     " omega: {}, const: {}, a: {}, b: {}, c: {}\n".format(time_min, self.alpha_best,
                                                                           self.gama_best, self.omega_best,
                                                                           self.const_best,
                                                                           self.a_best,
                                                                           self.b_best,
                                                                           self.c_best))
        print("Argument search Done")
        print("Best time cost: {}, alpha: {} gama: {},"
              " omega: {}, const: {}, a: {}, b: {}, c: {}\n".format(time_min, self.alpha_best,
                                                                    self.gama_best, self.omega_best,
                                                                    self.const_best,
                                                                    self.a_best,
                                                                    self.b_best,
                                                                    self.c_best))
        best_arg_dict = dict()
        best_arg_dict["omega"] = self.omega_best
        best_arg_dict["alpha"] = self.alpha_best
        best_arg_dict["gama"] = self.gama_best
        best_arg_dict["const"] = self.const_best
        best_arg_dict["time_cost"] = time_min
        best_arg_dict["a"] = self.a_best
        best_arg_dict["b"] = self.b_best
        best_arg_dict["c"] = self.c_best
        self.save_search_result(best_arg_dict, True)

    def set_omega(self, omega):
        self.omega = omega

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_gama(self, gama):
        self.gama = gama

    def set_const(self, const):
        self.const = const

    def save_search_result(self, arg_dict, best_tag=False):
        with open(self.arg_save_path, 'a+') as answer_file:
            if not best_tag:
                answer_file.write(
                    "omega: {}, alpha: {}, gama: {}, const: {}, time_cost: {}, a: {}, b: {}, c: {}\n".format(
                        arg_dict["omega"], arg_dict["alpha"], arg_dict["gama"],
                        arg_dict["const"], arg_dict["time_cost"], arg_dict["a"], arg_dict["b"], arg_dict["c"]))
            else:
                answer_file.write(
                    "Best argument omega: {}, alpha: {}, gama: {}, const: {}, time_cost: {}, a: {}, b: {}, c: {}\n".format(
                        arg_dict["omega"], arg_dict["alpha"], arg_dict["gama"],
                        arg_dict["const"], arg_dict["time_cost"], arg_dict["a"], arg_dict["b"], arg_dict["c"]))
