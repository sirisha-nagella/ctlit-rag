"""
Streamlit UI for the Clinical Trial & Literature RAG Assistant.
Run from project root: streamlit run app.py
"""
import streamlit as st


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
    with st.spinner("Searching and gathering..."):
        answer, hits, confident = ask(query)

    st.markdown("### Answer")
    if confident:
        st.write(answer)
    else:
        # gate refused - make it visually obvious this isn't a real answer
        st.info(answer)

    # always show what was retrieved, so the answer is auditable
    st.markdown("### Sources")
    st.caption(f"Closest match distance: {hits[0][2]:.3f}  "
               f"(threshold 0.50 - {'within' if confident else 'beyond'} range)")

    for doc, meta, dist in hits:
        source = meta["source"].replace("_", " ")
        ref = meta.get("nct_id") or meta.get("pmid")
        with st.expander(f"{ref} · {source} · distance {dist:.3f}"):
            st.write(doc)
