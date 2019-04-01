# -*- coding: utf-8 -*-
import logging
import sys

from solution.getSolution import GetSolution

logging.disable(logging.INFO)
logging.disable(logging.ERROR)


# logging.basicConfig(level=logging.DEBUG,
#                     filename='../logs/CodeCraft-2019.log',
#                     format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S',
#                     filemode='w+')


def main():
    if len(sys.argv) != 5:
        logging.info('please input args: car_path, road_path, cross_path, answerPath')
        exit(1)

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    answer_path = sys.argv[4]

    logging.info("car_path is %s" % (car_path))
    logging.info("road_path is %s" % (road_path))
    logging.info("cross_path is %s" % (cross_path))
    logging.info("answer_path is %s" % (answer_path))

    conf = car_path, road_path, cross_path, answer_path

    solution = GetSolution(conf)
    solution.load_data_and_build_graph()
    if solution.compute_result() < 0:
        # print("Solution result error")
        return -1
    solution.output_solution()

    # ********** 判题器 ***************
    # simulator = CheckAnswer(car_path, road_path, cross_path, answer_path)
    # simulate_result = simulator.simulating()
    # print("simulate_result: {}".format(simulate_result))

    # ********** 调参 ***************
    # omega = [2, 16, 64, 128, 256]
    # alpha = [1, 1 / 2, 1/8, 1/32, 1/128]
    # gama = [1, 1/2, 1/8, 1/16, 0]
    # const = [1, 2, 4, 16]

    # # ****************
    # # omega 已舍弃不用
    # omega = [64, ]
    # const = [1, ]
    #
    # # 上面两个参数不用调
    # alpha = [1, 1/6, 1/12]
    # gama = [1, 1 / 8, 1/16]
    # a = [1, 128, 512, 1024]
    # b = [1, 128, 512, 1024]
    # c = [1, 100, 10000, 100000]
    #
    # argument_dict = dict()
    # argument_dict["const"] = const
    # argument_dict["omega"] = omega
    # argument_dict["alpha"] = alpha
    # argument_dict["gama"] = gama
    # argument_dict["a"] = a
    # argument_dict["b"] = b
    # argument_dict["c"] = c
    #
    # print("argument_dict: {}".format(argument_dict))
    # adjust_arg = AdjustArg(conf, argument_dict=argument_dict)
    # adjust_arg.start_adjust_arg()


if __name__ == "__main__":
    main()
