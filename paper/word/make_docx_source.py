#!/usr/bin/env python3
"""paper/word/make_docx_source.py: turn paper/main.tex into a pandoc-friendly LaTeX file for the Word manuscript.

Plain-language summary: preprints.org requires a Word (.docx) manuscript. This script resolves every number,
figure, table, section, and citation reference from the compiled PDF build (main.aux, numbers.tex), so the
Word file says exactly what the PDF says. Then pandoc converts it and fix_tables.py tidies the tables.
Run after the PDF has been built.
"""
import os
import re

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tex = open(os.path.join(H, "main.tex")).read()
aux = open(os.path.join(H, "main.aux")).read()
labels = {m.group(1): m.group(2) for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux)}
cites = {m.group(1): int(m.group(2)) for m in re.finditer(r"\\bibcite\{([^}]+)\}\{\{(\d+)\}", aux)}
macros = {m.group(1): m.group(2) for m in
          re.finditer(r"\\newcommand\{\\(\w+)\}\{(.*)\}", open(os.path.join(H, "numbers.tex")).read())}


def compress(nums):
    nums = sorted(set(nums))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"{nums[i]}--{nums[j]}" if j - i >= 2 else ", ".join(map(str, nums[i:j + 1])))
        i = j + 1
    return "[" + ", ".join(out) + "]"


def expand(s):
    for _ in range(3):
        s = re.sub(r"\\(\w+)(?![a-zA-Z])", lambda m: macros.get(m.group(1), m.group(0)), s)
    return s


abstract = re.search(r"\\begin\{minipage\}\{0.82\\textwidth\}\s*\\small\s*(.*?)\\par\s*\\vspace\{4pt\}", tex, re.S).group(1)
keywords = re.search(r"\\textbf\{Keywords:\}(.*?)\n\\end\{minipage\}", tex, re.S).group(1).strip()
title = re.search(r"\{\\large\\bfseries (.*?)\\par\}", tex, re.S).group(1).replace("\\\\[2pt]", " ").replace("\n", " ")
body = tex[tex.index("\\section{Introduction}"):tex.index("\\end{thebibliography}") + len("\\end{thebibliography}")]

s = body.replace("\\FloatBarrier\n", "")
s = re.sub(r"\\begin\{adjustbox\}\{[^}]*\}(\\input\{[^}]*\})\\end\{adjustbox\}", r"\1", s)
s = re.sub(r"\\(scriptsize|footnotesize|small)\n", "", s)
s = s.replace("\\centering\\footnotesize", "\\centering").replace("\\centering\\small", "\\centering")
s = s.replace("\\begin{figure*}", "\\begin{figure}").replace("\\end{figure*}", "\\end{figure}")
s = s.replace("\\begin{table*}", "\\begin{table}").replace("\\end{table*}", "\\end{table}")
s = re.sub(r"\\begin\{(figure|table)\}\[[^\]]*\]", r"\\begin{\1}", s)
s = re.sub(r"\\includegraphics\[([^\]]*)\]\{([^}]+?)(\.pdf)?\}",
           lambda m: "\\includegraphics[width=" + ("4.0in" if "columnwidth" in m.group(1) else "6.4in") + "]{figures/"
           + os.path.basename(m.group(2)) + ".png}", s)
s = re.sub(r"\\input\{([^}]+)\}", lambda m: open(os.path.join(H, m.group(1))).read(), s)
s = s.replace("\\addlinespace", "")


def cap(m):
    env = m.group(0)
    lab = re.search(r"\\label\{([^}]+)\}", env)
    if not lab:
        return env
    num = labels[lab.group(1)]
    kind = "Figure" if lab.group(1).startswith("fig") else "Table"
    return re.sub(r"\\caption\{", lambda _: "\\caption{" + f"\\textbf{{{kind} {num}.}} ", env, count=1)


s = re.sub(r"\\begin\{(figure|table)\}.*?\\end\{\1\}", cap, s, flags=re.S)
s = re.sub(r"\\ref\{([^}]+)\}", lambda m: labels.get(m.group(1), "?"), s)
s = re.sub(r"\\cite\{([^}]+)\}", lambda m: compress([cites[k.strip()] for k in m.group(1).split(",")]), s)
s = s.replace("Fig.~", "Figure~")
s = re.sub(r"\\label\{[^}]+\}", "", s)

sec = sub = sss = 0
out = []
for line in s.split("\n"):
    m = re.match(r"\\(section|subsection|subsubsection)(\*?)\{(.*)\}(.*)$", line)
    if m and not m.group(2):
        kind, ttl, rest = m.group(1), m.group(3), m.group(4)
        if kind == "section":
            sec += 1
            sub = 0
            line = f"\\section*{{{'I II III IV V VI VII VIII'.split()[sec - 1]}. {ttl}}}{rest}"
        elif kind == "subsection":
            sub += 1
            sss = 0
            line = f"\\subsection*{{{chr(64 + sub)}. {ttl}}}{rest}"
        else:
            sss += 1
            line = f"\\textit{{{sss}. {ttl}.}} {rest}"
    out.append(line)
s = "\n".join(out)


def bib(m):
    items = re.findall(r"\\bibitem\{([^}]+)\}\s*(.*?)(?=\\bibitem|\\end\{thebibliography\})", m.group(0), re.S)
    return "\\section*{References}\n\n" + "\n\n".join(f"[{cites[k]}] {v.strip()}" for k, v in items)


s = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", bib, s, flags=re.S)
s = expand(s).replace("{,}", ",")
abstract = expand(abstract).replace("{,}", ",")

# inline math -> Unicode text, display equations kept as LaTeX math (pandoc writes Word equations)
SUP = str.maketrans("0123456789-+(),*kτ", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺⁽⁾˒*ᵏᵗ")
SUB = str.maketrans("0123456789ikbce", "₀₁₂₃₄₅₆₇₈₉ᵢₖ♭꜀ₑ")


INLINE = {
    "L_e": "Lₑ", "v^{\\rm class}_{c}": "v_class(c)", "v^{\\max}_e": "v_max(e)", "G=(V,E)": "G = (V, E)",
    "\\pi(x)": "π(x)", "\\mathcal{S}_k": "𝒮ₖ", "\\delta(u,w)": "δ(u, w)", "\\pi(s)": "π(s)",
    "t_{\\rm conn}(s)": "t_conn(s)", "T_b^{(k)}=\\infty": "T_b⁽ᵏ⁾ = ∞", "w_b": "w_b", "B_c": "B_c",
    "\\tau\\in\\{30,60\\}": "τ ∈ {30, 60}", "T_b^{(k)}": "T_b⁽ᵏ⁾"}


def uni(m):
    t = m.group(1)
    if t in INLINE:
        return INLINE[t].replace("_", "\\_")
    for a_, b_ in [("\\rho", "ρ"), ("\\tau", "τ"), ("\\infty", "∞"), ("\\,", "")]:
        t = t.replace(a_, b_)
    t = re.sub(r"\s*([=<>])\s*", r" \1 ", t).replace("  ", " ")
    return t.strip().replace("_", "\\_")


# display equations -> numbered PNG images (render reliably in Word, LibreOffice, and the preprints.org converter)
import subprocess  # noqa: E402
EQD = os.path.join(H, "word", "eq")
os.makedirs(EQD, exist_ok=True)
eq_n = [0]


def eq_img(m):
    eq_n[0] += 1
    n = eq_n[0]
    body_ = re.sub(r"\\label\{[^}]*\}", "", m.group(1)).strip()
    doc = ("\\documentclass[border=2pt,12pt]{standalone}\n\\usepackage{amsmath,amssymb}\n\\usepackage[sc]{mathpazo}\n"
           "\\begin{document}$\\displaystyle " + body_ + "$\\end{document}\n")
    open(os.path.join(EQD, f"eq{n}.tex"), "w").write(doc)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", f"eq{n}.tex"], cwd=EQD, stdout=subprocess.DEVNULL, check=True)
    subprocess.run(["pdftoppm", "-r", "600", "-png", "-singlefile", f"eq{n}.pdf", f"eq{n}"], cwd=EQD, check=True)
    from PIL import Image
    w_px = Image.open(os.path.join(EQD, f"eq{n}.png")).size[0]
    width_in = w_px / 600 * 0.95
    return (f"\n\n\\begin{{center}}\\includegraphics[width={width_in:.2f}in]{{word/eq/eq{n}.png}}"
            f"\\quad ({n})\\end{{center}}\n\n")


s = re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}", eq_img, s, flags=re.S)
parts = re.split(r"(\\begin\{equation\}.*?\\end\{equation\})", s, flags=re.S)
parts = [re.sub(r"\{\\rm (\w+)\}", r"{\\mathrm{\1}}", p).replace("\\\\[2pt]", "\\\\") if p.startswith("\\begin{equation}") else p
         for p in parts]
s = "".join(p if p.startswith("\\begin{equation}") else
            re.sub(r"(?<!\\)\$([^$]+?)(?<!\\)\$", uni, p.replace("\\$", "USDSIGN")).replace("USDSIGN", "\\$")
            for p in parts)
abstract = re.sub(r"(?<!\\)\$([^$]+?)(?<!\\)\$", uni, abstract)

head = r"""\documentclass{article}
\usepackage{amsmath}\usepackage{graphicx}\usepackage{booktabs}
\begin{document}
\begin{center}
\textbf{""" + title + r"""}
\end{center}

\begin{center}
Munachimso A. Emesobum$^{1,*}$
\end{center}

$^{1}$ Independent Researcher, Nevada, USA

$^{*}$ Correspondence: emesobumm@gmail.com; ORCID: https://orcid.org/0009-0002-7506-2153

\textbf{Abstract:} """ + abstract.strip() + "\n\n\\textbf{Keywords:} " + keywords + "\n\n"
open(os.path.join(H, "word", "manuscript_for_pandoc.tex"), "w").write(head + s + "\n\\end{document}\n")
print("ok", len(s))
