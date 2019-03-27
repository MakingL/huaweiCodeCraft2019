# -*- coding: utf-8 -*-
# @Time    : 2019/3/25 12:38
# @Author  : MLee
# @File    : AStar.py

from collections import deque


class AStar:
    def __init__(self, graph):
        self.graph = graph

    def distBetween(self, edge):
        """
        计算当前节点移动到邻居节点的代价
        :param edge: 当前节点与邻接节点的边
        :return: 代价值
        """
        return edge.weight

    def heuristicEstimate(self, start, goal):
        """
        计算启发函数值 h(n)
        :param start: 起始节点
        :param goal: 目标节点
        :return: h(n)
        """
        return 1

    def neighborNodes(self, current):
        """
        获得当前节点的邻居节点 字典 道路ID: 道路对象的字典
        :param current: 当前节点的 ID
        :return:
        """
        # neighbors = dict()
        # for edge in self.graph[current]:
        #     neighbors[edge.road_id] = edge
        #
        # return neighbors
        return self.graph.get_neighbors(current)

    def reconstructPath(self, cameFrom, goal):
        """
            重新建立路径完整信息
            :param cameFrom: 节点的父节点集合
            :param goal: 目标节点
            :return: 包含源节点 ID 到目标节点 ID 的路径
        """
        path = deque()
        node = goal
        path.appendleft(node)
        while node in cameFrom:
            node = cameFrom[node]
            path.appendleft(node)
        return path

    def getLowest(self, openSet, fScore):
        """
        获得 Open Set 中最低代价值得节点
        :param openSet:
        :param fScore:
        :return:
        """
        lowest = float("inf")
        lowestNode = None
        for node in openSet:
            if fScore[node] < lowest:
                lowest = fScore[node]
                lowestNode = node
        return lowestNode

    def aStar(self, start, goal):
        """
        A star 找 start 到 goal 节点的路径
        :param start:
        :param goal:
        :return:
        """
        cameFrom = {}
        openSet = set([start])
        closedSet = set()
        gScore = {}
        fScore = {}
        gScore[start] = 0
        fScore[start] = gScore[start] + self.heuristicEstimate(start, goal)
        while len(openSet) != 0:
            current = self.getLowest(openSet, fScore)
            if current == goal:
                return self.reconstructPath(cameFrom, goal)
            openSet.remove(current)
            closedSet.add(current)
            for neighbor, neighbor_road in self.neighborNodes(current):
                tentative_gScore = gScore[current] + self.distBetween(neighbor_road)
                if neighbor in closedSet and tentative_gScore >= gScore[neighbor]:
                    continue
                if neighbor not in closedSet or tentative_gScore < gScore[neighbor]:
                    cameFrom[neighbor] = current
                    gScore[neighbor] = tentative_gScore
                    fScore[neighbor] = gScore[neighbor] + self.heuristicEstimate(neighbor, goal)
                    if neighbor not in openSet:
                        openSet.add(neighbor)
        return 0
