from __future__ import annotations

import streamlit as st

from src.graph import run_log_analysis_workflow
from src.log_analyzer import SAMPLES, load_sample


def main() -> None:
    st.set_page_config(page_title="Multi-Agent Log Analyzer", layout="wide")
    st.title("Multi-Agent Log Analyzer")

    sample_name = st.selectbox("Sample log", sorted(SAMPLES))
    default_log = load_sample(sample_name)
    log_text = st.text_area("Log input", default_log, height=260)

    if st.button("Analyze logs", type="primary"):
        state = run_log_analysis_workflow(log_text)
        st.caption(f"Execution mode: {state['execution_mode']}")
        st.write("Completed graph nodes:", " -> ".join(state["completed_nodes"]))

        if state.get("warnings"):
            for warning in state["warnings"]:
                st.warning(warning)

        with st.expander("Parsed Issues", expanded=True):
            st.json([issue.model_dump() for issue in state["parsed_issues"]])
        with st.expander("Investigated Issues", expanded=True):
            st.json([issue.model_dump() for issue in state["investigated_issues"]])
        with st.expander("Priority Assessment", expanded=True):
            st.json(state["priority"].model_dump())
        if state.get("escalation"):
            with st.expander("Escalation Decision", expanded=True):
                st.json(state["escalation"].model_dump())
        with st.expander("Graph Trace", expanded=False):
            st.json([event.model_dump() for event in state["trace_events"]])

        st.markdown(state["report"])
        st.download_button("Download report", state["report"], "log_analysis_report.md")


if __name__ == "__main__":
    main()
