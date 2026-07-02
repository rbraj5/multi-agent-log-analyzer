from __future__ import annotations

import streamlit as st

from src.log_analyzer import SAMPLES, analyze_logs, load_sample


def main() -> None:
    st.set_page_config(page_title="Multi-Agent Log Analyzer", layout="wide")
    st.title("Multi-Agent Log Analyzer")

    sample_name = st.selectbox("Sample log", sorted(SAMPLES))
    default_log = load_sample(sample_name)
    log_text = st.text_area("Log input", default_log, height=260)

    if st.button("Analyze logs", type="primary"):
        report = analyze_logs(log_text)
        st.markdown(report)
        st.download_button("Download report", report, "log_analysis_report.md")


if __name__ == "__main__":
    main()
