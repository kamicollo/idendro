import sys
from pathlib import Path
from turtle import width

path = Path("./").absolute().parent
sys.path.insert(1, str(path))

import streamlit as st
st.set_page_config(layout="wide")
from demo_func import DemoData
import numpy as np
import scipy.cluster.hierarchy as sch
import idendro 
import importlib as imp


signals_to_generate = 100
network_cluster_count = 12
x_plot_labels = np.linspace(1, 1000, 1000)

demo = DemoData(no_signals=signals_to_generate, seed=833142, no_network_clusters = network_cluster_count)
signals = demo.generate_raw_data()

impairments = {
            "Suckout" : (20, "green", np.arange(300,370), 0.5 * (np.abs(np.arange(-35, 35)) - 35)),
            "Wave" : (12, "orange", np.arange(580,700), 3*np.sin(np.arange(120)/5)),
        }

tilt_x = np.arange(1000)
tilt_y = np.zeros(1000,)
tilt_y[demo.ideal_signal > 0] = -tilt_x[demo.ideal_signal > 0] * 0.02
impairments["Tilt"] = (19, "red", tilt_x, tilt_y)

graph, impaired_signals, network_clusters = demo.generate_impaired_graph(impairments=impairments)
sparse_matrix = demo.get_sparse_wavelet_matrix(impaired_signals)
dists = demo.get_adjacency_matrix(sparse_matrix)
model = sch.linkage(dists, method='average')
threshold = 70
cluster_assignments = sch.fcluster(model, threshold, criterion='distance')

idd = idendro.Idendro(model, cluster_assignments, threshold)
idd.dendrogram_kwargs.update({'leaf_label_func': idd.show_only_cluster_labels()})

def hovertext_func(point):
    _, tree = idd.get_tree()

    count = tree[point['id']].get_count()
    nodes = tree[point['id']].pre_order(lambda x: x.get_id() if x.is_leaf() else None)  
    sds = impaired_signals[nodes, :].std(axis=0)       
    return {
        "Number of items": count,
        "Type": point['type'],
        "Max st dev observed": sds.max().round(2)
    }

orientation = st.selectbox('orientation', ['top', 'bottom', 'right', 'left'], index=0)
component_value = idd.to_streamlit(key='o', width=1000, height=1000, orientation=orientation, scale_type='log', node_hover_func=hovertext_func)
st.write(component_value)

