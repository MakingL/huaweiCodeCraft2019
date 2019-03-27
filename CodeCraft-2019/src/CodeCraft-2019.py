import logging
import sys

from AStar.AStar import AStar
from Dijkstra.Dijkstra import Dijkstra
from Graph.GraphConf import Car, Road, Graph


class GetSolution(object):
    """docstring for GetSolution"""

    def __init__(self, conf_path):
        super(GetSolution, self).__init__()
        self.car_path, self.road_path, self.cross_path, self.answer_path = conf_path
        self.car_dict = dict()
        # self.road_dict = dict()
        # self.graph_dict = dict(set())
        self.graph = Graph()
        self.pending_car_list = list()

        # 有车辆访问过的道路id 集合
        self.road_set_traveled = set()
        self.road_weight_delta_dict = dict(dict())

        self.weight_update_list = list()

        # 可调参数
        self.schedule_batch_size = 0
        self.alpha = 0.5
        # self.weight_update_delta = 1

        self.omega = 4

    def load_data_and_build_graph(self):
        """
        导入输入数据并构建图
        :return:
        """
        # 读取车辆信息
        with open(self.car_path, 'r') as car_file:
            for line in car_file:
                line = line.strip(" \n()")
                if line == "" or line.startswith("#"):
                    continue
                data = line.replace(" ", "").replace("\t", "")
                car_id, car_from, car_to, car_speed, car_plan_time = data.split(",")
                car_conf = car_id, car_from, car_to, int(car_speed), int(car_plan_time)
                self.car_dict[car_id] = Car(car_conf)
                self.pending_car_list.append(self.car_dict[car_id])
                # self.car_list.append(Car(car_conf))

        logging.info("car count: {}".format(len(self.car_dict)))

        # 读取边的信息，建图
        road_count = 0
        with open(self.road_path, 'r') as road_file:
            for line in road_file:
                line = line.strip(" \n()")
                if line.startswith("#"):
                    continue
                data = line.replace(" ", "").replace("\t", "")
                road_id, road_len, speed_limit, chanel, start_id, end_id, bilateral = data.split(",")
                road_len, speed_limit, chanel = int(road_len), int(speed_limit), int(chanel)
                road_conf = road_id, int(road_len), int(speed_limit), int(chanel), start_id, end_id
                # self.road_dict[road_id] = Road(road_conf)
                new_road = Road(road_conf)
                # 正向边添加到图中
                # self.graph_dict[start_id].add(road_id)
                self.graph.add_edge(start_id, road_id, new_road)
                road_count += 1

                if bilateral == "1":
                    back_road_id = "{}_b".format(road_id)
                    road_conf = back_road_id, road_len, speed_limit, chanel, end_id, start_id
                    # self.road_dict[back_road_id] = Road(road_conf)
                    new_road = Road(road_conf)
                    # 反向边
                    # self.graph_dict[end_id].add(back_road_id)
                    self.graph.add_edge(end_id, back_road_id, new_road)

        # logging.info("vertex list: {}".format(self.graph.get_vertex_list()))
        logging.info("road count: {}".format(road_count))
        logging.info("load data complete")

    def compute_result(self):
        # 初始化调度参数
        self.schedule_batch_size = int(self.graph.get_vertex_count() *
                                       self.graph.get_average_chanel() / self.omega)

        logging.info("vertex count: {}".format(self.graph.get_vertex_count()))
        logging.info("schedule car batch size: {}".format(self.schedule_batch_size))

        # 预处理
        self.pre_process()
        # logging.info("pending car list: {}".format(self.get_pending_car_id_list()))

        time_slice = 0
        while True:
            # 无车待调度
            if not self.has_pending_car():
                logging.info("has no pending car in buffer! Done")
                break

            # 时间片加一
            time_slice += 1
            logging.info("time slice: {}".format(time_slice))

            # ****** 衰减图边上的权值 ******
            self.update_decay_graph_weight()

            # 从待调度的车辆 Buffer 中获得一批车辆
            car_scheduling_set = self.get_scheduling_car(time_slice)
            logging.info("got scheduling car set length: {}".format(len(car_scheduling_set)))

            weight_update_dict = dict()
            weight_update_dict.clear()
            for car in car_scheduling_set:
                # plan_path = self.get_a_star_path(self.graph_dict, car.car_from, car.car_to)
                # logging.info("schedule car: {}. Search node {} to node {}".format(car.car_id,
                #                 car.car_from, car.car_to))
                plan_path = self.get_dijkstra_path(self.graph, car.car_from, car.car_to)
                # logging.info("car: {} shortest path: {}".format(car.car_id, plan_path))

                self.car_dict[car.car_id].plan_path = plan_path
                # 车辆的真实出发时间
                self.car_dict[car.car_id].true_start_time = time_slice

                # ****** 更新边上的权值 ******
                self.update_graph_weight(plan_path, weight_update_dict, car.speed)

            # 道路访问的车辆数归一化处理
            for road_id in weight_update_dict:
                weight_update_dict[road_id]["times"] /= self.schedule_batch_size

            # 当前时间片的道路权值更新信息保存到列表
            self.weight_update_list.append(weight_update_dict)

        logging.info("total time slice: {}".format(time_slice))

    def output_solution(self):
        # 将结果写入到指定的输出文件
        with open(self.answer_path, 'w+') as answer_file:
            for car_id, car in self.car_dict.items():
                if len(car.plan_path) == 0:
                    logging.error("car: {} plan path is empty".format(car.car_id))
                path_str = car.plan_path.popleft()
                # for road_id in car.plan_path:
                while len(car.plan_path) != 0:
                    road_id = car.plan_path.popleft()
                    path_str += ",{}".format(road_id)
                answer_file.write("({},{},{})\n".format(car_id, car.true_start_time, path_str))

    def get_scheduling_car(self, time_slice):
        car_set = set()
        car_num = 0

        # logging.info("schedule_batch_size: {}".format(self.schedule_batch_size))
        # logging.info("car in pending list: {} length: {}".format(self.get_pending_car_id_list(),
        #                                                          len(self.pending_car_list)))
        for car in self.pending_car_list:
            # logging.info("car_num: {} time_slice: {} car id: {} car plan_time: {}".format(car_num,
            #                                                                               time_slice, car.car_id,
            #                                                                               car.plan_time))
            if car.plan_time <= time_slice:
                car_set.add(car)
                # logging.info("added car to scheduling set: {}".format(car.car_id))
                car_num += 1

                if car_num >= self.schedule_batch_size:
                    break

        for car in car_set:
            self.pending_car_list.remove(car)

        # if len(car_set) != 0:
        #     logging.info("has removed car in pending list: {}".format([car.car_id for car in car_set]))
        #     logging.info("remind car in pending list: {}, length: {}".format(self.get_pending_car_id_list(),
        #                                                                      len(self.pending_car_list)))

        return car_set

    def pre_process(self):
        """
        对车辆按照起始时间和速度进行升序排序
        :return:
        """
        self.pending_car_list.sort(key=lambda x: (x.plan_time, x.speed), reverse=False)

    def update_decay_graph_weight(self):
        for w_update in self.weight_update_list:
            for road_id in w_update:
                w_u = w_update[road_id]["weight"]
                beta = w_u * self.alpha * w_update[road_id]["times"]
                self.graph.change_edge_weight(road_id, (beta - 1) * w_u)
                w_update[road_id]["weight"] *= beta

        # for road_id in self.road_set_traveled:
        #     road_traveled_times = self.graph.get_edge_traveled_times(road_id)
        #     self.graph.decay_edge_weight(road_id, self.weight_decay_ratio * road_traveled_times)
        # road.weight *= (self.weight_decay_ratio * road.traveled_times)

    def update_graph_weight(self, path, weight_update_dict, car_speed):
        path_list = list(path)
        for i in range(len(path_list) - 1):
            start = path_list[i]
            end = path_list[i + 1]
            edge = self.graph.get_edge_obj(start, end)

            if edge is None:
                logging.error("edge {}:{} object is not exit".format(start, end))

            road_id = edge.road_id

            # for vertex_id in path:
            #     if road_id not in self.road_set_traveled:
            #         self.road_set_traveled.add(road_id)

            # 保存权值变化
            if road_id not in weight_update_dict:
                weight_update_dict[road_id] = dict()
                weight_update_dict[road_id]["weight"] = 0
                weight_update_dict[road_id]["times"] = 0

            weight_update_delta = self.graph.get_edge_weight_delta(road_id, car_speed)
            weight_update_dict[road_id]["weight"] += weight_update_delta
            weight_update_dict[road_id]["times"] += 1

            # 将权值的变化量存储起来
            # self.storage_weight_delta(car_id, road_id, weight_update_delta)

            # 更新道路上的权值
            self.graph.change_edge_weight(road_id, weight_update_delta)
            # self.graph.change_edge_travel_times(road_id, 1)

    def get_a_star_path(self, graph, source, destination):
        aStarSchedule = AStar(graph)
        return aStarSchedule.aStar(source, destination)

    def get_dijkstra_path(self, graph, car_from, car_to):
        """
        Dijkstra 算法搜索最短路
        :param graph:
        :param car_from:
        :param car_to:
        :return: (最短路队列， 最短路长度)
        """
        dijkstra = Dijkstra(graph)
        shortest_path, shortest_cost = dijkstra.dijkstra_search(car_from, car_to)
        return shortest_path

    def has_pending_car(self):
        return len(self.pending_car_list) != 0

    def get_pending_car_id_list(self):
        return [x.car_id for x in self.pending_car_list]

    def storage_weight_delta(self, car_id, road_id, weight_update_delta):
        if car_id not in self.road_weight_delta_dict:
            self.road_weight_delta_dict[car_id] = dict()

        self.road_weight_delta_dict[car_id][road_id] = weight_update_delta


logging.basicConfig(level=logging.DEBUG,
                    filename='../logs/CodeCraft-2019.log',
                    format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a+')


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


# to read input file
# process
# to write output file


if __name__ == "__main__":
    main()
