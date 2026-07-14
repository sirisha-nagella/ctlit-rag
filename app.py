"""
Streamlit UI for the Clinical Trial & Literature RAG Assistant.
Run from project root: streamlit run app.py
"""
import streamlit as st

from rag.feedback import log_feedback


@st.cache_resource
def load_pipeline():
    from scripts.ask import ask
    from rag.embedding_model import get_model
    get_model()          # warm the embedding model once
    return ask


ask = load_pipeline()


st.title("Clinical Trial & Literature RAG Assistant")
st.caption("Ask about Gilead trials and related published research. Answers are grounded in retrieved sources.")

query = st.text_input("Your question:", placeholder="e.g. What hepatitis B trials are there?")

if query:
    # Keyed on session state, not st.cache_data: st.cache_data's cache is
    # process-wide, so caching by query text there would mean the random
    # model pick and metrics logging only ever ran once per distinct
    # question, for the whole app, forever. Session state instead skips
    # re-running retrieval + the LLM on reruns *within this session*
    # (e.g. opening a source expander, clicking a feedback button) while
    # still giving every session's ask of a question its own A/B trial.
    if st.session_state.get("last_query") != query:
        st.session_state.last_query = query
        st.session_state.error = None
        with st.spinner("Searching and gathering..."):
            try:
                st.session_state.result = ask(query)
            except Exception as e:
                st.session_state.result = None
                st.session_state.error = str(e)

    if st.session_state.error:
        st.error(f"Something went wrong answering that question: {st.session_state.error}")
    else:
        answer, hits, confident, model_key, query_id = st.session_state.result

        st.markdown("### Answer")
        if confident:
            st.write(answer)
            if model_key:
                st.caption(f"Model: {model_key}")
        else:
            # gate refused - make it visually obvious this isn't a real answer
            st.info(answer)

        # feedback buttons - only meaningful when we actually generated an
        # answer (query_id is None for the no-match / low-confidence paths)
        if confident and query_id:
            feedback_key = f"feedback_{query_id}"
            if feedback_key not in st.session_state:
                st.session_state[feedback_key] = None

            col1, col2, col3 = st.columns([1, 1, 6])
            with col1:
                if st.button("👍", key=f"up_{query_id}"):
                    log_feedback(query_id, "up")
                    st.session_state[feedback_key] = "up"
            with col2:
                if st.button("👎", key=f"down_{query_id}"):
                    log_feedback(query_id, "down")
                    st.session_state[feedback_key] = "down"

            if st.session_state[feedback_key]:
                st.caption(f"Thanks — recorded your {st.session_state[feedback_key]} vote.")

        # always show what was retrieved, so the answer is auditable
        st.markdown("### Sources")
        if hits:
            st.caption(f"Closest match distance: {hits[0][2]:.3f}  "
                       f"(threshold 0.50 - {'within' if confident else 'beyond'} range)")

            for doc, meta, dist in hits:
                source = meta["source"].replace("_", " ")
                ref = meta.get("nct_id") or meta.get("pmid")
                with st.expander(f"{ref} · {source} · distance {dist:.3f}"):
                    st.write(doc)
        else:
            st.caption("No sources retrieved.")