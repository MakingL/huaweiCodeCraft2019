# -*- coding: utf-8 -*-
import logging
import sys

from simulator import CheckAnswer
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
    solution.compute_result()
    solution.output_solution()

    # 模拟，检验生成的答案
    simulator = CheckAnswer(car_path, road_path, cross_path, answer_path)
    simulator.simulating()


# to read input file
# process
# to write output file


if __name__ == "__main__":
    main()
