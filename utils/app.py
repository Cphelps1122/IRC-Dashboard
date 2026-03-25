import streamlit as st

def show_chart(fig):
    """
    Preferred chart renderer for pages that explicitly call it.
    """
    st.plotly_chart(
        fig,
        config={
            "scrollZoom": False,
            "displaylogo": False,
            "modeBarButtonsToRemove": [
                "zoom2d",
                "select2d",
                "lasso2d",
                "zoomIn2d",
                "zoomOut2d",
                "autoScale2d",
            ],
        },
        use_container_width=True,
    )

# ---------------------------------------------------------
# GLOBAL PATCH: override Streamlit's plotly_chart everywhere
# ---------------------------------------------------------

_original_plotly_chart = st.plotly_chart

def _patched_plotly_chart(fig, **kwargs):
    """
    Global override for ALL Plotly charts in the app.
    Ensures scroll zoom is disabled everywhere.
    """
    return _original_plotly_chart(
        fig,
        config={
            "scrollZoom": False,
            "displaylogo": False,
            "modeBarButtonsToRemove": [
                "zoom2d",
                "select2d",
                "lasso2d",
                "zoomIn2d",
                "zoomOut2d",
                "autoScale2d",
            ],
        },
        use_container_width=True,
    )

# Activate the global override
st.plotly_chart = _patched_plotly_chart
