# -*- coding: utf-8 -*-
# @Time    : 2019/3/25 12:51
# @Author  : MLee
# @File    : getSolution.py
import logging
import math

from AStar.AStar import AStar
from Dijkstra.Dijkstra import Dijkstra
from Floyd.Floyd import Floyd
from Graph.GraphConf import Car, Road, Graph


class GetSolution(object):
    """docstring for GetSolution"""

    def __init__(self, conf_path):
        super(GetSolution, self).__init__()
        self.car_path, self.road_path, self.cross_path, self.answer_path = conf_path
        # car id 到 car 对象的映射
        self.car_dict = dict()

        # 地图对象
        self.graph = Graph()

        # 等待调度的车辆列表
        self.pending_car_list = list()

        # Floyd 算法对象
        self.Floyd = None

        # 权值更新的列表
        self.weight_update_list = list()

        self.graph_vertex_count = 0
        self.graph_average_chanel = 0
        # ******** 可调参数 *********
        # Num_CarPerTime 即 每时间切片调度的车辆大小
        self.schedule_batch_size = 0

        # 计算 Num_CarPerTime 中的参数 w
        self.omega = 21

        # 权值衰减公式中的参数 a
        self.alpha = 1 / 6

        self.weight_update_const = 1
        self.weight_update_dict = dict()

        self.gama = 0.5

        # 车辆 batch size 的二次函数参数
        self.batch_c = 20
        self.batch_b = 1500
        self.batch_a = 2.2e-6

    def get_schedule_batch_size(self, time_slice):
        # logging.info("time_slice: {}".format(time_slice))
        # logging.info("(time_slice - self.batch_b) ** 2: {}".format(time_slice - self.batch_b ** 2))
        # # print("(time_slice - self.batch_b) ** 2: {}".format(time_slice - self.batch_b ** 2))

        # self.omega = -self.batch_a * ((time_slice - self.batch_b) ** 2) + self.batch_c

        # logging.info("omega: {}".format(self.omega))
        # logging.info("N*C: {}".format(self.graph_vertex_count * self.graph_average_chanel))
        # # print("N*C: {}".format(self.graph_vertex_count * self.graph_average_chanel))

        # result = int(self.graph_vertex_count * self.graph_average_chanel / self.omega)

        # # print("result: {}".format(result))
        # logging.info("result: {}".format(result))

        result = int(self.graph.get_vertex_count() *
                     self.graph.get_average_chanel() / self.omega)
        return result

    def compute_result(self):
        self.graph_vertex_count = self.graph.get_vertex_count()
        self.graph_average_chanel = self.graph.get_average_chanel()

        # 初始化调度参数
        self.schedule_batch_size = int(self.graph.get_vertex_count() *
                                       self.graph.get_average_chanel() / self.omega)

        # 防止计算出来的值小于 1
        self.schedule_batch_size = max(1, self.schedule_batch_size)
        #
        # logging.info("schedule car batch size: {}".format(self.schedule_batch_size))

        # 预处理，对待调度的车辆进行排序
        self.pre_process()
        # logging.info("pending car list: {}".format(self.get_pending_car_id_list()))

        # logging.info("initial edge weight")
        # for e_id, edge in self.graph.edge_dict.items():
        #     logging.info("edge: {} weight: {}".format(e_id, edge.weight))

        time_slice = 0
        while True:
            # 获取动态的车辆调度
            # self.schedule_batch_size = self.get_schedule_batch_size(time_slice)
            # # 防止计算出来的值小于 1
            # self.schedule_batch_size = max(1, self.schedule_batch_size)
            # logging.info("schedule car batch size: {}".format(self.schedule_batch_size))
            # print("schedule car batch size: {}".format(self.schedule_batch_size))

            # 无车待调度
            if not self.has_pending_car():
                # logging.info("has no pending car in buffer! Done")
                break

            # 时间片加一
            time_slice += 1
            # logging.info("time slice: {}".format(time_slice))
            # print("time slice: {}".format(time_slice))

            # ****** 衰减图边上的权值 ******
            self.update_decay_graph_weight()

            # 从待调度的车辆 Buffer 中获得一批车辆
            car_scheduling_set = self.get_scheduling_car(time_slice)
            # logging.info("got scheduling car set length: {}".format(len(car_scheduling_set)))

            weight_update_dict = dict()
            weight_update_dict.clear()
            for car in car_scheduling_set:
                # logging.info("schedule car: {}. Search node {} to node {}".format(car.car_id,
                #                                                                   car.car_from, car.car_to))

                # ***** A* 算法调度 ********
                # print("starting search shortest path")
                plan_path = self.get_a_star_path(self.graph, car.car_from, car.car_to)
                # 存在负权值边
                if plan_path is None:
                    return -2
                # logging.info("car: {} shortest path: {}".format(car.car_id, plan_path))
                # print("got shortest path")

                # ***** Dijkstra 算法调度 *****
                # plan_path, cost = self.get_dijkstra_path(self.graph, car.car_from, car.car_to)
                # logging.info("car: {} shortest path: {} cost: {}".format(car.car_id, plan_path, cost))

                # 将路径由节点的序列转换为道路的序列
                path_list = self.trans_path_to_road(plan_path)

                # 该车辆调度已确定，car 对象可删除
                self.car_dict[car.car_id].plan_path_list = path_list
                # 车辆的真实出发时间
                self.car_dict[car.car_id].true_start_time = time_slice

                # ****** 更新边上的权值 ******
                self.update_graph_weight(path_list, weight_update_dict, car.speed)

            # 道路访问的车辆数归一化处理
            for road_id in weight_update_dict:
                weight_update_dict[road_id]["times"] /= self.schedule_batch_size

            # 当前时间片的道路权值更新信息保存到列表
            self.weight_update_list.append(weight_update_dict)
            # logging.info("time slice: {} weight_update_list len: {}".format(time_slice, len(self.weight_update_list)))
            # logging.info("time slice: {} weight_update_list: {}".format(time_slice, self.weight_update_list))

        logging.info("total schedule time slice: {}".format(time_slice))
        return time_slice

    def load_data_and_build_graph(self):
        """
        导入输入数据并构建图
        :return:
        """

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
                road_conf = road_id, road_len, speed_limit, chanel, start_id, end_id

                new_road = Road(road_conf)
                # 正向边添加到图中
                self.graph.add_edge(start_id, road_id, new_road)
                road_count += 1

                if bilateral == "1":
                    # 反向边的 id 为 “正向边 id_b”
                    back_road_id = "{}_b".format(road_id)
                    road_conf = back_road_id, road_len, speed_limit, chanel, end_id, start_id

                    new_road = Road(road_conf)
                    # 反向边添加到图中
                    self.graph.add_edge(end_id, back_road_id, new_road)

        logging.info("road count: {}".format(road_count))
        logging.info("vertex count: {}".format(self.graph.get_vertex_count()))
        # logging.info("load data complete")

        # Floyd 求任意两点的最短距离，A* 算法用，预处理车辆排序也用
        self.Floyd = Floyd(self.graph)
        # logging.info("Floyd init complete")

        road_avg_speed = self.graph.get_average_road_speed()

        # 读取车辆信息
        with open(self.car_path, 'r') as car_file:
            for line in car_file:
                line = line.strip(" \n()")
                if line == "" or line.startswith("#"):
                    continue
                data = line.replace(" ", "").replace("\t", "")
                car_id, car_from, car_to, car_speed, car_plan_time = data.split(",")

                # 车辆在道路上行驶的期望时间
                exp_drive_len = self.Floyd.get_dist(car_from, car_to)
                exp_cost_time = exp_drive_len / min(road_avg_speed, int(car_speed)) + int(car_plan_time)

                car_conf = car_id, car_from, car_to, int(car_speed), int(car_plan_time), exp_cost_time

                self.car_dict[car_id] = Car(car_conf)
                self.pending_car_list.append(self.car_dict[car_id])

        logging.info("car count: {}".format(len(self.car_dict)))

    def output_solution(self):
        """
        输出该地图的调度结果到 answer 文件
        :return:
        """
        # 将结果写入到指定的输出文件
        with open(self.answer_path, 'w+') as answer_file:
            for car_id, car in self.car_dict.items():
                path_str = ",".join(car.plan_path_list)
                answer_file.write("({},{},{})\n".format(car_id, car.true_start_time, path_str))

    def get_scheduling_car(self, time_slice):
        """
        获得当前时间片可以调度的车辆集合
        :param time_slice: 当前时间片
        :return:
        """
        car_set = set()
        car_num = 0

        for car in self.pending_car_list:
            if car.plan_time <= time_slice:
                car_set.add(car)
                car_num += 1

                if car_num >= self.schedule_batch_size:
                    break

        for car in car_set:
            self.pending_car_list.remove(car)

        return car_set

    def pre_process(self):
        """
        # 对车辆按照起始时间和速度进行升序排序

        修改为：对车辆按照在地图上行驶的期望时间和速度进行排序
        :return:
        """
        self.pending_car_list.sort(key=lambda x: (x.plan_time, x.speed), reverse=False)
        # self.pending_car_list.sort(key=lambda x: (x.plan_time, -x.speed), reverse=False)
        # self.pending_car_list.sort(key=lambda x: (x.exp_cost_time, x.speed), reverse=False)
        # self.pending_car_list.sort(key=lambda x: (x.exp_cost_time, -x.speed), reverse=False)

    def update_decay_graph_weight(self):
        """
        道路权值衰减
        :return:
        """
        for w_update in self.weight_update_list:
            for road_id in w_update:
                w_u = w_update[road_id]["weight"]
                # if w_u < 0:
                #     logging.info("road_id: {} w_u: {}".format(road_id, w_u))
                if w_u <= 1e-5:
                    w_update[road_id]["weight"] = 0
                    continue

                # print('w_update[road_id]["times"]: {}'.format(w_update[road_id]["times"]))
                beta = self.alpha * w_update[road_id]["times"]
                # print("beta - 1: {}".format(beta - 1))

                decayed_weight = (beta - 1) * w_u
                w_update[road_id]["weight"] *= beta
                change_before, after_decayed_weight = self.graph.change_edge_weight(road_id, decayed_weight)
                if after_decayed_weight < 0:
                    logging.error(
                        "road_id: {} change_before: {} decayed_weight: {}"
                        " after_decayed_weight: {}".format(road_id,
                                                           change_before,
                                                           decayed_weight,
                                                           after_decayed_weight))

    def update_graph_weight(self, road_path_list, weight_update_dict, car_speed):
        """
        道路权值更新
        :param road_path_list:
        :param weight_update_dict:
        :param car_speed:
        :return:
        """
        for road_id in road_path_list:
            edge = self.graph.get_edge_form_id(road_id)

            if edge is None:
                logging.error("edge {}: object is not exit".format(road_id))

            edge_start_id = edge.start_id
            edge_chanel = edge.chanel
            vertex_degree = self.graph.get_vertex_degree(edge_start_id)
            speed_min = min(car_speed, edge.speed_limit)
            gama = vertex_degree * edge_chanel / speed_min

            # 加 1 防止生成负的权值变化量
            gama += self.weight_update_const
            weight_update_delta = math.log(gama)

            if weight_update_delta < 1e-5:
                weight_update_delta = 0

            # 保存权值变化
            if road_id not in weight_update_dict:
                weight_update_dict[road_id] = dict()
                weight_update_dict[road_id]["weight"] = 0
                weight_update_dict[road_id]["times"] = 0

            # 计算权值变化量，并保存
            # weight_update_delta = self.graph.get_edge_weight_delta(road_id, car_speed)
            weight_update_dict[road_id]["weight"] += weight_update_delta
            weight_update_dict[road_id]["times"] += 1

            if weight_update_delta < 0:
                logging.error("update road {} weight: {}".format(road_id, weight_update_delta))

            # 更新道路上的权值
            change_before, change_after = self.graph.change_edge_weight(road_id, weight_update_delta)
            # logging.info(
            #     "update weight road_id: {} change_before: {} weight_update_delta: {} change_after: {}".format(
            #         road_id,
            #         change_before,
            #         weight_update_delta,
            #         change_after))

    def get_a_star_path(self, graph, source, destination):
        """
        用 A* 计算得到规划的最短路径
        :param graph:
        :param source:
        :param destination:
        :return:
        """
        aStarSchedule = AStar(graph, self.Floyd, self.gama)
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

        return shortest_path, shortest_cost

    def has_pending_car(self):
        """
        是否存在待调度的车辆
        :return:
        """
        return len(self.pending_car_list) != 0

    def get_pending_car_id_list(self):
        return [x.car_id for x in self.pending_car_list]

    def trans_path_to_road(self, plan_path):
        """
        将路径由图的顶点 id 序列 转换为 边的 id 序列
        :param plan_path:
        :return:
        """
        path_road = list()
        path_road.clear()

        start_node = plan_path.popleft()
        while len(plan_path) != 0:
            end_node = plan_path.popleft()
            edge_id = self.graph.get_adjacent_edge_id(start_node, end_node)
            path_road.append(edge_id)
            start_node = end_node

        return path_road

    def set_argument(self, omega=None, alpha=None, gama=None, const_data=None, batch_a=None, batch_b=None,
                     batch_c=None):
        if omega is not None:
            self.omega = omega
        if alpha is not None:
            self.alpha = alpha
        if gama is not None:
            self.gama = gama
        if const_data is not None:
            self.weight_update_const = const_data
        if batch_a is not None:
            self.batch_a = batch_a
        if batch_b is not None:
            self.batch_b = batch_b
        if batch_c is not None:
            self.batch_c = batch_c
