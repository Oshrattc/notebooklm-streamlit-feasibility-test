"""NotebookLM Integration Test page. Experiment only; invented documents only.
One button runs one test through the visitor's own experimental NotebookLM bridge extension; see README.md."""
import secrets
import time

import streamlit as st

from nlm_common import EXPERIMENT_PREFIX, accept_result, bridge, fictional_documents, show_result

QUESTION = ('According to the fictional examination report, which claims are rejected and on what grounds, and which '
            'claims require further examination or appear allowable? Cite the report.')


def unique_title(state):
    """A notebook title no other run, tab or user of this page will produce: time plus a per-session random tag."""
    tag = state.setdefault('online_tag', secrets.token_hex(3))
    return f"{EXPERIMENT_PREFIX}online {time.strftime('%Y%m%d-%H%M%S')} {tag}"


def remember(state, result):
    """Records a notebook this session created, so that only this session can offer to delete it."""
    created = state.setdefault('online_created', [])
    step = (result.get('steps') or {}).get('create') or {}
    if step.get('ok') and step.get('notebookId') and not any(c['id'] == step['notebookId'] for c in created):
        created.append({'id': step['notebookId'], 'title': step.get('title', '')})
    if result.get('type') == 'delete' and result.get('ok'):
        gone = result['deleted']['id']
        state['online_created'] = [c for c in created if c['id'] != gone]


def main():
    st.set_page_config(page_title='NotebookLM Integration Test', layout='centered')
    st.title('NotebookLM Integration Test')
    st.caption('Experiment only. Invented documents only. Requires the experimental NotebookLM bridge Chrome extension in '
               'this Chrome profile and a NotebookLM sign-in. Results are AI-generated and unverified.')
    state = st.session_state
    files, texts = fictional_documents()
    if 'online_next_title' not in state:
        state.online_next_title = unique_title(state)

    st.markdown(f"**Next test notebook:** `{state.online_next_title}`  \n**Question:** {QUESTION}")
    values = [bridge(['combined'], 'online_run', new_title=state.online_next_title, question=QUESTION, files=files)]
    created = state.get('online_created', [])
    if created:
        last = created[-1]
        st.caption(f"Clean up: delete the notebook this session created last ({last['title']}).")
        values.append(bridge(['delete'], 'online_delete', delete_id=last['id'], delete_title=last['title']))

    for key, value in values:
        accepted = accept_result(state, value, key)
        if accepted is None:
            continue
        state.online_last = accepted
        remember(state, accepted)
        if key == 'online_run':
            state.online_next_title = unique_title(state)
        st.rerun()

    if state.get('online_last'):
        show_result(state.online_last, texts, QUESTION)


if __name__ == '__main__':
    main()
