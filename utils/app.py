import streamlit as st

def show_chart(fig):
    """
    Global Plotly chart renderer.
    Disables scroll zoom everywhere and cleans up the toolbar.
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

# Optional: Monkey‑patch Streamlit's plotly_chart globally
def _patched_plotly_chart(fig, **kwargs):
    st.plotly_chart(
        fig,
        config={
            "scrollZoom": False,
            "displaylogo": False,
        },
        use_container_width=True,
    )

# Uncomment this line to force ALL pages to use the patched version
# st.plotly_chart = _patched_plotly_chart
