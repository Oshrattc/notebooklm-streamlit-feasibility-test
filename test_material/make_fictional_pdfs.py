"""Creates the two harmless, entirely invented PDF documents used by the NotebookLM feasibility tests.

They are not real patent documents. Every sentence is fictional and written for this test. The examination report has two
pages, with known text on each page, so that a citation's passage and page can be checked against the source.

Run: python make_fictional_pdfs.py   (writes fictional_claims.pdf and fictional_examination_report.pdf next to this file)
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

HERE = Path(__file__).resolve().parent

CLAIMS = [
    ('title', 'Fictional Patent Claims'),
    ('p', 'Document reference: FICTIONAL-CLAIMS-001. Invented for software testing only. Not a real patent application.'),
    ('p', 'Claim 1: A device comprising a red housing, a blue switch, and a removable battery.'),
    ('p', 'Claim 2: The device of claim 1, wherein the blue switch activates a light source.'),
    ('p', 'Claim 3: The device of claim 2, wherein the light source emits green light.'),
    ('p', 'Claim 4: The device of claim 1, wherein the removable battery is held in place by a sliding cover.'),
]

REPORT_PAGE_1 = [
    ('title', 'Fictional Examination Report'),
    ('p', 'Document reference: FICTIONAL-REPORT-001. Invented for software testing only. Not a real examination report.'),
    ('h', 'Cited documents'),
    ('p', 'Reference A: a fictional brochure describing a torch with a red housing, a blue switch and a removable battery.'),
    ('p', 'Reference B: a fictional catalogue describing a lamp whose battery is held in place by a sliding cover.'),
    ('h', 'Novelty'),
    ('p', 'Claim 1 is rejected for lack of novelty because Reference A discloses a red housing, a blue switch, and a '
          'removable battery.'),
    ('p', 'Claim 2 requires further examination because Reference A does not disclose the light source activated by '
          'the blue switch.'),
]

REPORT_PAGE_2 = [
    ('h', 'Inventive step'),
    ('p', 'Claim 4 is rejected for lack of inventive step because combining Reference A with Reference B, which shows a '
          'battery held by a sliding cover, would have been obvious to the skilled person.'),
    ('p', 'Claim 3 appears to involve an inventive step, because neither Reference A nor Reference B mentions green light.'),
    ('h', 'Conclusion'),
    ('p', 'The applicant is invited to file amended claims within four fictional months.'),
]


def build(path, blocks_by_page):
    styles = getSampleStyleSheet()
    kind = {'title': styles['Title'], 'h': styles['Heading2'], 'p': styles['BodyText']}
    story = []
    for page_no, blocks in enumerate(blocks_by_page):
        if page_no:
            story.append(PageBreak())
        for k, text in blocks:
            story += [Paragraph(text, kind[k]), Spacer(1, 6)]
    SimpleDocTemplate(str(path), pagesize=A4, title=blocks_by_page[0][0][1], author='Fictional test material').build(story)


if __name__ == '__main__':
    build(HERE / 'fictional_claims.pdf', [CLAIMS])
    build(HERE / 'fictional_examination_report.pdf', [REPORT_PAGE_1, REPORT_PAGE_2])
    print('written:', ', '.join(p.name for p in sorted(HERE.glob('*.pdf'))))
