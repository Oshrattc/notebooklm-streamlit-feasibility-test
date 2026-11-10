# NotebookLM Integration Test

A standalone feasibility experiment: can a hosted Streamlit page drive Google NotebookLM in the visitor's own browser,
through a browser extension, without ever handling the visitor's Google credentials?

It uses only two invented documents (`test_material/*.pdf`, marked "Invented for software testing only"). They are not
real patent documents.

What it does: one button asks the visitor's own experimental NotebookLM bridge Chrome extension (unpublished, not
available from any store) to create a uniquely named notebook in the visitor's own NotebookLM, upload the two invented
PDFs, ask one fixed question and read the citations. Without that extension the page does nothing. The page never
receives Google passwords, cookies or tokens; results arrive only over the visitor's own Streamlit session, and are kept
only in that session's memory.

The extension accepts requests from this page only after its exact address has been added to the extension's trusted
list. Even then, the extension itself (not this page) allows only one fixed workflow: notebooks titled with the
experiment's fixed prefix followed by "online <date-time> <tag>", only the two invented PDFs in test_material (checked by
SHA-256), only the one fixed question, and only notebooks it created for this page in the same browser session, never
the visitor's own notebooks. Changing this page's code cannot widen that.

Run locally (this computer only): `run_locally_windows.bat`, then open http://localhost:8503.

Files: see MANIFEST.txt (SHA-256 of every file).
