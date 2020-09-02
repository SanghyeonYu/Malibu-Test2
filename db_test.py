import pandas as pd
import numpy as np
import time
import csv

class csv_writer():
    def __init__(self, path, name):
        ## 아웃풋 파일 경로 설정
        path_output = path
        path_output = "/data_csv/"

        with open(path_output + name, mode='w', encoding='utf-8-sig') as file_writer:
            writer = csv.writer(file_writer, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(column_list)

            for subgraph in nx.weakly_connected_components(act_network):
                if len(subgraph) == 1:
                    for n in subgraph:
                        try:
                            temp_list = []
                            temp_list.append(n)
                            temp_list.append(act_network.in_degree(n))
                            temp_list.append(act_network.out_degree(n))
                            for attr in act_network.nodes[n].values():
                                temp_list.append(attr)
                            # print(temp_list)
                            writer.writerow(temp_list)

                        except:
                            pass


