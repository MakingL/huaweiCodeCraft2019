# -*- coding: utf-8 -*-
# @Time    : 2019/3/28 22:43
# @Author  : MLee
# @File    : AdjustArg.py
import logging
import time

from Simulator.Simulator import CheckAnswer
from solution.getSolution import GetSolution


class AdjustArg(object):
    """docstring for AdjustArg"""

    def __init__(self, conf, omega=None, alpha=None, gama=None, const=None):
        super(AdjustArg, self).__init__()
        self.conf = conf

        self.omega = omega
        self.alpha = alpha
        self.gama = gama
        self.const = const

        self.alpha_best = 0
        self.gama_best = 0
        self.omega_best = 0
        self.const_best = 0

        # car_path, road_path, cross_path, answer_path = self.conf
        # self.simulator = CheckAnswer(car_path, road_path, cross_path, answer_path)

        self.arg_save_path = "./arg_info.txt"

    def start_adjust_arg(self):
        total_epoch = len(self.omega) * len(self.alpha) * len(self.gama) * len(self.const)
        search_epoch = 0
        # search_progress = 0
        last_progress = 0

        time_min = float("inf")

        print("Start search argument...")
        for omega in self.omega:
            for alpha in self.alpha:
                for gama in self.gama:
                    for const in self.const:
                        # 搜索进度信息
                        search_epoch += 1
                        search_progress = search_epoch / total_epoch * 100
                        if search_progress - last_progress >= 5:
                            last_progress = search_progress
                            print("Argument search progress: {}%".format(search_progress))

                        start_time = time.clock()
                        solution = GetSolution(self.conf)
                        solution.set_argument(omega=omega, alpha=alpha, gama=gama, const_data=const)
                        solution.load_data_and_build_graph()
                        time_slice = solution.compute_result()
                        if time_slice < 0:
                            continue
                        solution.output_solution()

                        # 模拟，检验生成的答案
                        car_path, road_path, cross_path, answer_path = self.conf
                        simulator = CheckAnswer(car_path, road_path, cross_path, answer_path)
                        simulate_result = simulator.simulating()
                        if simulate_result < 0:
                            continue
                        end_time = time.clock()
                        time_cost = end_time - start_time

                        if time_cost < time_min:
                            time_min = time_cost
                            self.alpha_best = alpha
                            self.gama_best = gama
                            self.omega_best = omega
                            self.const_best = const
                            logging.info("Get a better time cost: {}, alpha: {} gama: {},"
                                         " omega: {}, const: {}\n".format(time_min, self.alpha_best,
                                                                          self.gama_best, self.omega_best,
                                                                          self.const_best))
                        # print("Get a better time cost: {}, alpha: {} gama: {},"
                        #       " omega: {}, const: {}\n".format(time_min, self.alpha_best,
                        #                                        self.gama_best, self.omega_best,
                        #                                        self.const_best))
                        arg_dict = dict()
                        arg_dict["omega"] = omega
                        arg_dict["alpha"] = alpha
                        arg_dict["gama"] = gama
                        arg_dict["const"] = const
                        arg_dict["time_cost"] = time_cost
                        self.save_search_result(arg_dict, False)
            logging.info("Argument search Done")
            logging.info("Best time cost: {}, alpha: {} gama: {},"
                         " omega: {}, const: {}\n".format(time_min, self.alpha_best,
                                                          self.gama_best, self.omega_best,
                                                          self.const_best))
            print("Argument search Done")
            print("Best time cost: {}, alpha: {} gama: {},"
                  " omega: {}, const: {}\n".format(time_min, self.alpha_best,
                                                   self.gama_best, self.omega_best,
                                                   self.const_best))
            best_arg_dict = dict()
            best_arg_dict["omega"] = self.omega_best
            best_arg_dict["alpha"] = self.alpha_best
            best_arg_dict["gama"] = self.gama_best
            best_arg_dict["const"] = self.const_best
            best_arg_dict["time_cost"] = time_min
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
                answer_file.write("omega: {}, alpha: {}, gama: {}, const: {}, time_cost: {}\n".format(
                    arg_dict["omega"], arg_dict["alpha"], arg_dict["gama"],
                    arg_dict["const"], arg_dict["time_cost"]))
            else:
                answer_file.write("Best argument omega: {}, alpha: {}, gama: {}, const: {}, time_cost: {}\n".format(
                    arg_dict["omega"], arg_dict["alpha"], arg_dict["gama"],
                    arg_dict["const"], arg_dict["time_cost"]))
