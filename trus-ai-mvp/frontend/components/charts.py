import pandas as pd
import streamlit as st


def approval_pie_chart(approvals: int, denials: int):
    data = pd.DataFrame(
        {
            "Outcome": ["Approved", "Denied"],
            "Count": [approvals, denials],
        }
    )
    st.plotly_chart(
        {
            "data": [
                {
                    "values": data["Count"],
                    "labels": data["Outcome"],
                    "type": "pie",
                    "hole": 0.3,
                }
            ],
            "layout": {"height": 400, "margin": {"l": 0, "r": 0, "t": 0, "b": 0}},
        },
        use_container_width=True,
    )

