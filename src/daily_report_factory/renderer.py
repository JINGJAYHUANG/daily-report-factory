from __future__ import annotations

from html import escape
from typing import Any

from .catalog import PublicationSpec
from .contracts import IssueDocument, validate_issue_or_raise

_CSS = r"""
:root{--ink:#172033;--muted:#64748b;--line:#cbd5e1;--paper:#fff;--wash:#f1f5f9;--accent:#155e75;--accent2:#9a3412;--max:1380px}
*{box-sizing:border-box}
html,body{margin:0;max-width:100%;overflow-x:hidden;background:var(--wash);color:var(--ink)}
body{font-family:Arial,"Noto Sans SC",sans-serif;line-height:1.55}
a{color:var(--accent);text-underline-offset:3px;overflow-wrap:anywhere}
img,svg,video,canvas{max-width:100%;height:auto}
code,pre,p,li,dd,dt,h1,h2,h3,h4,span,strong{overflow-wrap:anywhere;word-break:normal}
.report-shell{width:min(var(--max),100%);margin:0 auto;padding:28px}
.issue-header{background:var(--ink);color:#fff;padding:clamp(28px,5vw,68px);border-radius:18px;margin-bottom:22px}
.issue-kicker{font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;color:#bae6fd;font-weight:700}
h1{font-size:clamp(2rem,5vw,4.8rem);line-height:1.02;margin:.4rem 0 1rem;max-width:18ch}
.issue-subtitle{font-size:clamp(1rem,2vw,1.35rem);max-width:72ch;color:#e2e8f0}
.issue-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}.pill{border:1px solid #475569;border-radius:999px;padding:5px 10px;font-size:.78rem}
.report-section,.report-page{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:clamp(22px,4vw,52px);margin:0 0 22px;min-width:0}
.report-page{min-height:720px;display:flex;flex-direction:column}
.section-index{font-size:.75rem;font-weight:700;color:var(--accent2);letter-spacing:.12em;text-transform:uppercase}
h2{font-size:clamp(1.5rem,3vw,2.8rem);line-height:1.12;margin:.45rem 0 .8rem}.summary{font-size:1.05rem;max-width:78ch}
.grid{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,.65fr);gap:22px;margin-top:24px;min-width:0}
.panel{border-top:3px solid var(--accent);padding-top:12px;min-width:0}.panel h3{margin:.15rem 0 .55rem;font-size:1rem;text-transform:uppercase;letter-spacing:.06em}
ul{padding-left:1.2rem}.evidence-list{display:grid;gap:10px}.evidence-card{border:1px solid var(--line);border-radius:12px;padding:14px;background:#f8fafc;min-width:0}
.source-chip{display:inline-block;margin:7px 6px 0 0;padding:2px 7px;border-radius:999px;background:#e0f2fe;color:#0c4a6e;font-size:.72rem;font-weight:700}
.sources,.disclosures{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;margin-top:22px;min-width:0}
.source-list{display:grid;gap:12px}.source-item{border-bottom:1px solid var(--line);padding-bottom:10px;min-width:0}.source-item:last-child{border:0}
.table-wrap{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}table{border-collapse:collapse;width:100%;min-width:640px}th,td{border:1px solid var(--line);padding:8px;text-align:left}
footer{font-size:.78rem;color:var(--muted);padding:18px 4px 42px}
@media(max-width:720px){.report-shell{padding:12px}.issue-header,.report-section,.report-page,.sources,.disclosures{border-radius:10px;padding:20px}.grid{grid-template-columns:1fr}.report-page{min-height:0}h1{font-size:2.25rem}}
@media print{body{background:#fff}.report-shell{width:100%;padding:0}.issue-header{border-radius:0}.report-page{break-after:page;border:0;border-radius:0;min-height:100vh;margin:0}.report-page:last-of-type{break-after:auto}.sources,.disclosures{break-inside:avoid}a{color:inherit;text-decoration:none}}
"""


def _list(items: list[str]) -> str:
    if not items:
        return '<p class="muted">None specified.</p>'
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _evidence(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">No evidence items supplied.</p>'
    cards: list[str] = []
    for item in items:
        chips = "".join(f'<span class="source-chip">{escape(source_id)}</span>' for source_id in item["source_ids"])
        cards.append(f'<div class="evidence-card"><strong>{escape(item["claim"])}</strong><div>{chips}</div></div>')
    return '<div class="evidence-list">' + "".join(cards) + "</div>"


def _section(section: dict[str, Any], index: int, total: int, mode: str) -> str:
    css_class = "report-page" if mode == "paged" else "report-section"
    return f'''<article class="{css_class}" id="{escape(section['id'])}" data-section-kind="{escape(section['kind'])}" data-page-index="{index}">
      <div class="section-index">{index:02d} / {total:02d} · {escape(section['kind'])}</div>
      <h2>{escape(section['heading'])}</h2>
      <p class="summary">{escape(section['summary'])}</p>
      <div class="grid">
        <section class="panel"><h3>Evidence</h3>{_evidence(section.get('evidence', []))}</section>
        <div>
          <section class="panel"><h3>Implications</h3>{_list(section.get('implications', []))}</section>
          <section class="panel"><h3>Actions / watchpoints</h3>{_list(section.get('actions', []))}</section>
        </div>
      </div>
    </article>'''


def render_issue(issue: IssueDocument, spec: PublicationSpec) -> str:
    validate_issue_or_raise(issue, spec)
    data = issue.data
    sections = "\n".join(_section(section, index, len(issue.sections), spec.mode) for index, section in enumerate(issue.sections, 1))
    sources = "".join(
        f'''<div class="source-item" id="source-{escape(source['id'])}">
          <strong>{escape(source['id'])} · {escape(source['title'])}</strong><br>
          <span>{escape(source['publisher'])} · published {escape(source['published_at'])} · checked {escape(source['checked_at'])}</span><br>
          <a href="{escape(source['url'], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(source['url'])}</a><br>
          <small>Rights note: {escape(source['rights'])}</small>
        </div>'''
        for source in issue.sources
    )
    disclosures = _list(data["disclosures"])
    mode_label = "paged" if spec.mode == "paged" else "long-scroll"
    return f'''<!doctype html>
<html lang="{escape(data['language'], quote=True)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="Daily Report Factory 0.1.0">
  <meta name="publication-id" content="{escape(spec.publication_id, quote=True)}">
  <meta name="issue-id" content="{escape(data['issue_id'], quote=True)}">
  <title>{escape(data['title'])} · {escape(spec.title)}</title>
  <style>{_CSS}</style>
</head>
<body data-publication-mode="{mode_label}" data-synthetic="{str(data['synthetic']).lower()}">
  <main class="report-shell">
    <header class="issue-header">
      <div class="issue-kicker">{escape(spec.title)} · {escape(spec.title_zh)}</div>
      <h1>{escape(data['title'])}</h1>
      <p class="issue-subtitle">{escape(data['subtitle'])}</p>
      <div class="issue-meta"><span class="pill">Issue {escape(data['issue_date'])}</span><span class="pill">{mode_label}</span><span class="pill">Contract {escape(spec.contract_version)}</span><span class="pill">Status: {escape(data['status'])}</span></div>
    </header>
    {sections}
    <section class="sources" id="sources"><h2>Source register</h2><div class="source-list">{sources}</div></section>
    <section class="disclosures" id="disclosures"><h2>Disclosures and limits</h2>{disclosures}</section>
    <footer>Rendered deterministically from structured JSON. Generated-at metadata: {escape(data['generated_at'])} · Timezone: {escape(data['timezone'])}.</footer>
  </main>
</body>
</html>
'''
