from scipy.cluster.hierarchy import dendrogram # type: ignore
import numpy as np
import numpy.typing as npt

from typing import Callable, Dict, List, Tuple, Union
from .cluster_info import ClusteringData
from .types_classes import (
    ClusterLink,
    ClusterNode,
    Dendrogram,
    ScipyDendrogram,
    AxisLabel,
)

class BaseDendro:
    cluster_data: Union[ClusteringData, None]
    icoord: npt.NDArray[np.float32] = np.ndarray(0)
    dcoord: npt.NDArray[np.float32] = np.ndarray(0)
    link_colors: List[str] = []
    leaf_labels: List[str] = []
    leaf_positions: List[float] = []
    leaves: List[int] = []
    leaves_color_list: List[str] = []
    node_dict: Dict[Tuple[float, float], ClusterNode] = {}
    color_scheme: Dict[str, str] = {}

    def __init__(
        self,
        color_scheme: Dict[str, str] = None,
    ) -> None:
        if color_scheme is None:            
            self.color_scheme = {
                'C0': '#1f77b4',
                'C1': '#ff7f0e',
                'C2': '#2ca02c',
                'C3': '#d62728',
                'C4': '#9467bd',
                'C5': '#8c564b',
                'C6': '#e377c2',
                'C7': '#7f7f7f',
                'C8': '#bcbd22',
                'C9': '#17becf'
            }
        else:
            self.color_scheme = color_scheme


    def convert_scipy_dendrogram(
        self,
        R: ScipyDendrogram,
        compute_nodes: bool = True,
        node_label_func: Callable[[ClusteringData, ClusterNode], str] = None,
        node_hover_func: Callable[[ClusteringData, ClusterNode], Dict[str, str]] = None,
    ) -> Dendrogram:
        """Converts a dictionary representing a dendrogram generated by SciPy to Idendro dendrogram object

        Args:
            R (ScipyDendrogram): Dictionary as generated by scipy.cluster.hierarchy.dendrogram(*, no_plot=True) or equivalent
            node_label_func (Callable[[], str], optional): Callback function to generate dendrogram node labels. See create_dendrogram() for usage details.
            node_hover_func (Callable[[], Union[Dict, str]], optional): Callback function to generate dendrogram hover text labels. See create_dendrogram() for usage details.

        Returns:
            Dendrogram: Idendro dendrogram object
        """

        self._set_scipy_dendrogram(R)

        dendrogram = self._generate_dendrogram(
            compute_nodes=compute_nodes,
            node_label_func=node_label_func,
            node_hover_func=node_hover_func,
        )

        return dendrogram

    def set_cluster_info(self, cluster_data: ClusteringData) -> None:          
        self.cluster_data = cluster_data     

    def create_dendrogram(
        self,
        truncate_mode: str = "level",
        p: int = 4,
        sort_criteria: str = "distance",
        sort_descending: bool = False,
        link_color_func: Callable[[int], str] = None,
        leaf_label_func: Callable[[int], str] = None,
        compute_nodes: bool = True,
        node_label_func: Callable[[ClusteringData, ClusterNode], str] = None,
        node_hover_func: Callable[[ClusteringData, ClusterNode], Dict[str, str]] = None,
        
    ) -> Dendrogram:

        # if we don't have a scipy dendrogram yet, create one
        if self.icoord.shape[0] == 0:            
            R = self._create_scipy_dendrogram(
                truncate_mode=truncate_mode,
                p=p,
                sort_criteria=sort_criteria,
                sort_descending=sort_descending,
                link_color_func=link_color_func,
                leaf_label_func=leaf_label_func,
            )
            self._set_scipy_dendrogram(R)

        # proceed to create a dendrogram object
        dendrogram = self._generate_dendrogram(
            compute_nodes=compute_nodes,
            node_label_func=node_label_func,
            node_hover_func=node_hover_func,
        )

        return dendrogram

    def _set_scipy_dendrogram(self, R: ScipyDendrogram) -> None:
        """Validates and sets SciPy-format dendrogram.

        Args:
            R (ScipyDendrogram): SciPy-format dendrogram

        Raises:
            AttributeError: if the dictionary is not of SciPy format
        """
        required_keys = [
            "icoord",
            "dcoord",
            "color_list",
            "ivl",
            "leaves",
            "leaves_color_list",
        ]

        missing_keys = set(required_keys).difference(set(R.keys()))
        if missing_keys:
            raise AttributeError(
                "SciPy Dendrogram passed is missing keys '{}'".format(
                    ", ".join(missing_keys)
                )
            )

        self.icoord = np.array(R["icoord"])
        self.dcoord = np.array(R["dcoord"])
        self.link_colors = R["color_list"]
        self.leaf_labels = R["ivl"]
        self.leaves = R["leaves"]
        self.leaves_color_list = R["leaves_color_list"]

        X = self.icoord.flatten()
        Y = self.dcoord.flatten()
        self.leaf_positions = np.sort(X[Y == 0.0]).tolist()

    def _create_scipy_dendrogram(
        self,
        truncate_mode: str,
        p: int,
        sort_criteria: str,
        sort_descending: bool,
        link_color_func: Callable[[int], str] = None,
        leaf_label_func: Callable[[int], str] = None,
    ) -> ScipyDendrogram:
        """Uses SciPy to generate a dendrogram object

        Args:
            truncate_mode ('str'): truncate mode that takes values 'lastp', 'level' or None. Refer to create_dendrogram() for details.
            p (int): criterion for truncate mode. Refer to create_dendrogram() for details
            sort_criteria (str): sort criteria that takes values 'count' or 'distance'. Refer to create_dendrogram() for details.
            sort_descending (bool): sort direction. 
            link_color_func (Callable[[int], str]): callback function to generate link and node colors. Refer to create_dendrogram() for details.
            leaf_label_func (Callable[[int], str]): callback function to generate leaf labels. Refer to create_dendrogram() for details.

        Returns:
            ScipyDendrogram: SciPy-format dendrogram dictionary
        """

        if self.cluster_data is None:
            raise RuntimeError(
                "Clustering data was not provided (idendro.set_cluster_info()), cannot generate dendrogram."
            )

        kwargs = dict(    
            Z=self.cluster_data.linkage_matrix,
            truncate_mode=truncate_mode,
            p=p,
            link_color_func=link_color_func,
            leaf_label_func=leaf_label_func,            
            no_plot=True,
        )

        # translate sort arguments to scipy interface
        assert sort_criteria in ["distance", "count"], ValueError(
            "sort_criteria can be only 'distance' or 'count'"
        )
        if sort_criteria == "distance":
            kwargs['distance_sort'] = "descending" if sort_descending else "ascending"
            kwargs['count_sort'] = False            
        elif sort_criteria == "count":
            kwargs['count_sort'] = "descending" if sort_descending else "ascending"
            kwargs['distance_sort'] = False            

        # generate scipy dendrogram
        return dendrogram(**kwargs)


    def _generate_dendrogram(
        self,      
        compute_nodes: bool,  
        node_label_func: Callable[[ClusteringData, ClusterNode], str] = None,
        node_hover_func: Callable[[ClusteringData, ClusterNode], Dict[str, str]] = None,
    ) -> Dendrogram:
        
        links = self._links()
        axis_labels = self._axis_labels()

        
        nodes = self._nodes(
            node_label_func=node_label_func, node_hover_func=node_hover_func
        ) if compute_nodes else []
        
        return Dendrogram(links=links, axis_labels=axis_labels, nodes=nodes)

    def _links(self) -> List[ClusterLink]:
        return [
            ClusterLink(x=x, y=y, fillcolor=self.color_scheme[color])
            for x, y, color in zip(self.icoord, self.dcoord, self.link_colors)
        ]

    def _axis_labels(self) -> List[AxisLabel]:
        return [
            AxisLabel(label=l, x=x)
            for x, l in zip(self.leaf_positions, self.leaf_labels)
        ]

    def _nodes(
        self, 
        node_label_func: Callable[[ClusteringData, ClusterNode], str] = None,
        node_hover_func: Callable[[ClusteringData, ClusterNode], Dict[str, str]] = None
    ) -> List[ClusterNode]:

        if not self.node_dict:

            if self.cluster_data is None:
                raise RuntimeError(
                    "Clustering data was not provided (idendro.set_cluster_info()), cannot compute nodes."
                )


            #first, create node objects for each leaf
            for xcoord, leaf_id, color in zip(
                self.leaf_positions, self.leaves, self.leaves_color_list
            ):

                p = ClusterNode(
                    x=xcoord,
                    y=0,
                    edgecolor=self.color_scheme[color],
                    fillcolor=self.color_scheme[color],
                    radius=4.,
                    type="leaf",
                    cluster_id=None,
                    id=leaf_id
                )

                p.label = node_label_func(self.cluster_data, p) if node_label_func is not None else ""
                p.hovertext = node_hover_func(self.cluster_data, p) if node_hover_func is not None else {}

                self.node_dict[(xcoord, 0)] = p

            #then, we traverse all the other links and associate them with leaves
            # this approach works because links in a scipy.dendrogram are generated in the same order as leaves and sequentially
            # so we can be always sure that a link has its "leafs" are present in our dictionary
            merge_map = self.cluster_data.get_merge_map()
            leaders, flat_cluster_ids = self.cluster_data.get_leaders()

            for x, y, color in zip(self.icoord, self.dcoord, self.link_colors):
                left_coords = (x[0], y[0])
                right_coords = (x[3], y[3])
                right_leaf = self.node_dict[right_coords]
                left_leaf = self.node_dict[left_coords]
                merged_id = merge_map[(left_leaf.id, right_leaf.id)]

                cluster_id = None
                if merged_id in leaders:
                    node_type = "cluster"
                    cluster_id = flat_cluster_ids[leaders == merged_id][0]
                elif right_leaf.type in ["leaf", "subcluster"] and left_leaf.type in ["leaf", "subcluster"]:
                    node_type = "subcluster"
                else:
                    node_type = "supercluster"

                merged_coords = (x[1] + (x[2] - x[1]) / 2.0, y[2])

                p = ClusterNode(
                    x=merged_coords[0],
                    y=merged_coords[1],
                    edgecolor=self.color_scheme[color],                    
                    type=node_type,
                    cluster_id=cluster_id,
                    id=merged_id
                )

                if node_type != 'subcluster':
                    p.fillcolor = self.color_scheme[color]

                p.label = node_label_func(self.cluster_data, p) if node_label_func is not None else ""
                p.hovertext = node_hover_func(self.cluster_data, p) if node_hover_func is not None else {}

                self.node_dict[merged_coords] = p        

        return list(self.node_dict.values())

    