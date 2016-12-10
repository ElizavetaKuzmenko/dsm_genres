import os
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def distance_graph(root, query, distances, nodes): 
    ok = True
    plotFile = "%s.png" % (query)
    if not plotFile in os.listdir(root + 'data/distance_graphs/'):
        G = nx.Graph()
        G.add_nodes_from(set(nodes))
        for x in distances: 
            if not x[1] == 1 and not 'all' in x[0]:
                if x[1] == np.nan:
                    image_path = 'data/distance_graphs/error.png'
                    ok = False
                    break 
                else:
                    G.add_edge(x[0][0], x[0][1], weight=1-x[1])
        if ok:
            labels = nx.get_edge_attributes(G,'weight')
            edges, weights = zip(*labels.items())
            pos = nx.spring_layout(G)
            plt.figure(figsize=(10,6))
            plt.axis('off')
            nx.draw(G,pos, with_labels=True, node_size=2300, font_size=10, font_color='#1a2e1a', node_color='#84e786', \
                    alpha=0.8, node_shape="o", edgelist=edges, edge_color=weights, width=8.0, edge_cmap=plt.cm.Blues)
            nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
            nx.write_graphml(G, 'data/distance_graphs/'+query+'.graphml')
            plt.savefig(root + 'data/distance_graphs/' + query + '.png', dpi=150, bbox_inches='tight')
            plt.clf()
    if ok:
        image_path = 'data/distance_graphs/' + plotFile

    return image_path
