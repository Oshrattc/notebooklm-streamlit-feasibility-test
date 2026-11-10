"""Helpers of the NotebookLM feasibility test page: the extension component, per-session request ids,
the invented PDFs, the citation check and the result display. Holds no Google credentials."""
import base64
import json
import re
import secrets
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

HERE = Path(__file__).resolve().parent
# Next to this file in the public test package; one folder up in the experiment.
MATERIAL = HERE / 'test_material' if (HERE / 'test_material').is_dir() else HERE.parent / 'test_material'
FICTIONAL_PDFS = ('fictional_claims.pdf', 'fictional_examination_report.pdf')
EXPERIMENT_PREFIX = 'WIPO feasibility test - '

DEFAULT_TITLE = 'Extension test notebook'
DEFAULT_QUESTION = 'According to the source, what are the three components of the fictional invention?'
EXPECTED_TERMS = ('red housing', 'blue switch', 'removable battery')
COMBINED_QUESTION = ('According to the fictional examination report, which claims are rejected and on what grounds, '
                     'and which claims require further examination or appear allowable? Cite the report.')

_bridge = components.declare_component('nlm_bridge', path=str(HERE / 'component'))


def new_request_id():
    return secrets.token_hex(16)


def request_id(state, key):
    """The current request id of one component (each component has its own, held in this session only)."""
    ids = state.setdefault('nlm_request_ids', {})
    if key not in ids:
        ids[key] = new_request_id()
    return ids[key]


def accept_result(state, value, key='default'):
    """Returns the extension's result if it answers this session's current request for component `key`, else None. Each
    accepted result retires that component's request id, so a stale or repeated value is never shown twice. Ids are per
    component: a reply to one component (for example "busy") can never retire another component's pending request."""
    if not isinstance(value, dict) or value.get('request_id') != request_id(state, key):
        return None
    state['nlm_request_ids'][key] = new_request_id()
    return value


def expected_terms_found(answer):
    lower = (answer or '').lower()
    return {term: term in lower for term in EXPECTED_TERMS}


def _letters(text):
    return re.sub(r'[^a-z0-9]+', '', (text or '').lower())


def verify_passage(passage, documents, source_title=''):
    """Checks a passage returned by NotebookLM against the fictional source documents' own text.

    documents: {file name: [text of page 1, text of page 2, ...]}. Comparison ignores case, spaces and punctuation.
    Returns {'result': 'verified' | 'partly' | 'not found' | 'no passage', 'document': name or '', 'pages': [1-based]}.
    The passage is split into sentences so that a passage running over a page break is still found."""
    sentences = [s for s in re.split(r'(?<=[.:;])\s+', passage or '') if len(_letters(s)) >= 20]
    if not sentences:
        return {'result': 'no passage', 'document': '', 'pages': []}
    names = sorted(documents, key=lambda n: n != source_title)  # the cited source first
    best = {'result': 'not found', 'document': '', 'pages': []}
    for name in names:
        pages = [_letters(p) for p in documents[name]]
        joined = ''.join(pages)
        hits = [s for s in sentences if _letters(s) in joined]
        if not hits:
            continue
        found_pages = sorted({i + 1 for s in hits for i, p in enumerate(pages) if _letters(s)[:40] in p})
        result = 'verified' if len(hits) == len(sentences) else 'partly'
        if best['result'] != 'verified':
            best = {'result': result, 'document': name, 'pages': found_pages}
    return best


@st.cache_data
def fictional_documents():
    """The fictional PDFs: bytes (base64, for the extension) and page texts (for verification). Built if missing."""
    from pypdf import PdfReader
    import io
    if not all((MATERIAL / n).is_file() for n in FICTIONAL_PDFS):
        import runpy
        runpy.run_path(str(MATERIAL / 'make_fictional_pdfs.py'), run_name='__main__')
    files, texts = [], {}
    for name in FICTIONAL_PDFS:
        data = (MATERIAL / name).read_bytes()
        files.append({'name': name, 'base64': base64.b64encode(data).decode('ascii')})
        texts[name] = [page.extract_text() or '' for page in PdfReader(io.BytesIO(data)).pages]
    return files, texts


def bridge(actions, key, **args):
    value = _bridge(actions=list(actions), request_id=request_id(st.session_state, key), key=key, default=None, **args)
    return key, value


def show_result(last, texts, current_question=None):
    st.divider()
    kind = last.get('type', '')
    st.subheader(f'Result: {kind}')
    if not last.get('ok'):
        st.error(f"{last.get('code', 'ERROR')}: {last.get('message', '')}")
        if last.get('pageMessage'):
            st.text(last['pageMessage'])
    elif kind == 'diagnose':
        st.json(last.get('diagnosis', {}))
    elif kind == 'upload':
        st.success(f"Added and processed in {last.get('elapsedMs', 0) / 1000:.1f} s: "
                   + ', '.join(u['name'] for u in last.get('uploaded', [])))
    elif kind == 'create':
        st.success(f"Created \"{last.get('title')}\" in {last.get('elapsedMs', 0) / 1000:.1f} s.")
    elif kind == 'delete':
        st.success(f"Deleted \"{(last.get('deleted') or {}).get('title', '')}\".")
    if last.get('ok') and last.get('answer') is not None:
        sent = last.get('questionSent')
        if sent:
            st.markdown(f'**Question sent:** {sent}')
            if current_question is not None and sent.strip() != current_question.strip():
                st.warning('This answer is for the question shown above, which differs from the text now in the question box '
                           '(the box was changed, or the button was clicked before the page had taken the new text).')
        st.markdown('**NotebookLM answer (AI-generated, unverified)**')
        st.text(last.get('answer', ''))
        if last.get('followUp'):
            st.caption('NotebookLM follow-up suggestion (not part of the answer): ' + last['followUp'])
        st.caption(f"Notebook: {last.get('notebookTitle', '')} · {last.get('elapsedMs', 0) / 1000:.1f} s · "
                   f"NotebookLM tab was {'the active tab' if last.get('notebookTabActive') else 'a background tab'} "
                   f"({last.get('visibilityState', '?')}) · question confirmed above answer: {last.get('questionConfirmed')}")
        markers = last.get('citationMarkers') or []
        st.markdown(f"**Citation markers in the answer:** {', '.join(markers) if markers else 'none'}")
        if kind == 'ask' and last.get('notebookTitle', '').startswith(DEFAULT_TITLE):
            found = expected_terms_found(last.get('answer'))
            st.markdown('**Expected-answer check:** ' + ', '.join(f"{t} {'✓' if ok else '✗'}" for t, ok in found.items()))
        details = last.get('citationDetails')
        if details:
            if not details.get('ok'):
                st.warning(f"Citation details: {details.get('code')}: {details.get('message')}")
            rows = []
            for c in details.get('citations', []):
                check = verify_passage(c.get('passage', ''), texts, c.get('sourceTitle', ''))
                rows.append({'marker': c.get('marker'), 'source shown': c.get('sourceTitle'), 'read via': c.get('via'),
                             'passage shown by NotebookLM': c.get('passage'),
                             'page shown by NotebookLM': c.get('page') or 'not shown',
                             'check against fictional PDF': check['result'], 'found in': check['document'],
                             'PDF page(s)': ', '.join(map(str, check['pages']))})
            st.markdown('**Citation details** (passage as shown by NotebookLM; the check compares it with the fictional PDF text)')
            st.dataframe(rows, hide_index=True)
    with st.expander('Raw result'):
        st.code(json.dumps(last, ensure_ascii=False, indent=1), language='json')
