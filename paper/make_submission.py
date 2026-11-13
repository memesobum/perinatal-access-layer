#!/usr/bin/env python3
"""paper/make_submission.py: assemble the preprints.org upload set in paper/submission/.

Plain-language summary: after the paper, the Word file, the graphic abstract, and the supplementary PDF are built,
this script makes the figures-and-tables package (every figure as a 300-dpi PNG and a PDF, plus one PDF with every
figure and table on its own page, numbered as in the manuscript) and copies the five upload files into one folder.

Upload map (preprints.org form field -> file):
  Manuscript File (docx)   Emesobum_2026_Manuscript.docx
  PDF Version              Emesobum_2026_Manuscript.pdf
  Graphic Abstract         Graphic_Abstract.png
  Figures and Tables       Figures_and_Tables.zip
  Supplementary File       Supplementary_Materials.pdf
"""
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

H = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.join(H, "submission")
os.makedirs(SUB, exist_ok=True)
tex = open(os.path.join(H, "main.tex")).read()
aux = open(os.path.join(H, "main.aux")).read()
labels = {m.group(1): m.group(2) for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux)}
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12}

items = []
for env in re.finditer(r"\\begin\{(figure\*?|table\*?)\}(?:\[[^\]]*\])?(.*?)\\end\{\1\}", tex, re.S):
    body = env.group(2)
    lab = re.search(r"\\label\{([^}]+)\}", body).group(1)
    kind = "fig" if lab.startswith("fig") else "tab"
    n = int(labels[lab]) if kind == "fig" else ROMAN[labels[lab]]
    items.append((kind, n, body))

with tempfile.TemporaryDirectory() as tmp:
    pre = tex[:tex.index("\\begin{document}")]
    pre = re.sub(r"\\documentclass\[[^\]]*\]\{(\w+)\}", r"\\documentclass[11pt]{\1}", pre, count=1)
    out = ["\\begin{document}",
           "\\begin{center}{\\large\\bfseries Figures and Tables}\\\\[4pt]{\\small Emesobum, How Far to Perinatal Care? "
           "(preprint). Numbering matches the manuscript.}\\end{center}"]
    for kind in ("fig", "tab"):
        for k, n, body in sorted(x for x in items if x[0] == kind):
            env = "figure" if kind == "fig" else "table"
            b = body.replace("\\columnwidth", "0.8\\textwidth")
            out.append(f"\\clearpage\\begin{{{env}}}[p]\\setcounter{{{env}}}{{{n - 1}}}{b}\\end{{{env}}}")
    out.append("\\end{document}")
    open(os.path.join(tmp, "ft.tex"), "w").write(pre + "\n".join(out))
    shutil.copy(os.path.join(H, "numbers.tex"), tmp)
    shutil.copytree(os.path.join(H, "tables"), os.path.join(tmp, "tables"))
    shutil.copytree(os.path.join(H, "figures"), os.path.join(tmp, "figures"))
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "ft.tex"], cwd=tmp, stdout=subprocess.DEVNULL, check=True)
    zp = os.path.join(SUB, "Figures_and_Tables.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(tmp, "ft.pdf"), "Figures_and_Tables.pdf")
        for k, n, body in sorted(x for x in items if x[0] == "fig"):
            f = re.search(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", body).group(1).replace(".pdf", "")
            for ext in ("png", "pdf"):
                z.write(os.path.join(H, "figures", f"{f}.{ext}"), f"Figure_{n:02d}.{ext}")

shutil.copy(os.path.join(H, "main.pdf"), os.path.join(SUB, "Emesobum_2026_Manuscript.pdf"))
shutil.copy(os.path.join(H, "word", "Emesobum_manuscript.docx"), os.path.join(SUB, "Emesobum_2026_Manuscript.docx"))
for f in sorted(os.listdir(SUB)):
    print(f"{os.path.getsize(os.path.join(SUB, f)) / 1e6:7.2f} MB  {f}")
