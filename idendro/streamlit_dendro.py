import os
import streamlit.components.v1 as components
import json


_RELEASE = False

if not _RELEASE:
    _component_func = components.declare_component(
        "idendro-dendrogram",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("idendro", path=build_dir)


class StreamlitFeatures():
    def to_streamlit(self, key=None):
        """Create a new instance of "idendro".

        Parameters
        ----------
        key: str or None
            An optional key that uniquely identifies this component. If this is
            None, and the component's arguments are changed, the component will
            be re-mounted in the Streamlit frontend and lose its current state.

        Returns
        -------
        int
            The number of times the component's "Click Me" button has been clicked.
            (This is the value passed to `Streamlit.setComponentValue` on the
            frontend.)

        """
        dendrogram = self.to_json()
        component_value = _component_func(data=dendrogram, key=key, default=0)
        return component_value