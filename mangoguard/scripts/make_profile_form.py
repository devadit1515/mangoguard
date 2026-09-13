"""Rebuild STUDENT_PROFILE.md from structured content.

The criteria checklist is a table whose cells hold several paragraphs each, which a
markdown pipe table cannot carry. Pandoc's grid tables can, but only if every border
lines up to the character, and hand-aligning fifteen rows across three columns is a way
to introduce silent corruption: an edit that lengthens one cell by a character breaks the
table, and pandoc then reads the whole thing as running text rather than failing loudly.

So the table is generated. Content lives in `artifacts/_profile_rows.json` as paragraphs,
and this script does the wrapping and the alignment. Edit the JSON, run this, rebuild the
Word file.

Reproduce with:  python scripts/make_profile_form.py
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROWS = ROOT / "artifacts" / "_profile_rows.json"
OUT = ROOT / "STUDENT_PROFILE.md"

WIDTHS = (34, 24, 74)


def _cell_lines(paragraphs: list[str], width: int) -> list[str]:
    lines: list[str] = []
    for i, para in enumerate(paragraphs):
        if i:
            lines.append("")
        lines.extend(textwrap.wrap(para, width) or [""])
    return lines


def _rule(char: str = "-") -> str:
    return "+" + "+".join(char * (w + 2) for w in WIDTHS) + "+"


def _render(cells: list[list[str]], header: bool = False) -> str:
    cols = [_cell_lines(c, w) for c, w in zip(cells, WIDTHS, strict=True)]
    height = max(len(c) for c in cols)
    out = []
    for i in range(height):
        parts = [
            " " + (col[i] if i < len(col) else "").ljust(w) + " "
            for col, w in zip(cols, WIDTHS, strict=True)
        ]
        out.append("|" + "|".join(parts) + "|")
    out.append(_rule("=" if header else "-"))
    return "\n".join(out)


def build_table(data: dict) -> str:
    parts = [_rule(), _render(data["header"], header=True)]
    parts.extend(_render(row) for row in data["rows"])
    return "\n".join(parts)


PREAMBLE = """# CREST Awards — Student profile

> **Working draft, 4 September 2026.** Transcribe into the official CREST Student Profile Form
> before submission. Page numbers exist only after the final PDF export and must be re-checked after
> any re-export, so the "Where" column marks them TBC. Two criteria are recorded as not yet met
> rather than padded, because the project is at its simulation stage and the orchard season has not
> arrived.

+------------------------------------+----------------------------------------------------------+
| First name                         | Devadit                                                  |
| *Please provide only the first     |                                                          |
| name of the student or team        |                                                          |
| member. Do not include middle or   |                                                          |
| last names.*                       |                                                          |
+------------------------------------+----------------------------------------------------------+
| CREST Award Level                  | Gold                                                     |
+------------------------------------+----------------------------------------------------------+
| Project title                      | Counting Fruit a Camera Cannot See: Estimating Mango     |
|                                    | Load from Few Viewpoints                                 |
+------------------------------------+----------------------------------------------------------+
| Mentor name                        | -                                                        |
| *(if you had one)*                 |                                                          |
+------------------------------------+----------------------------------------------------------+

"""

TAIL = """

## Personal reflections

*Now that you've finished your project, use this space to add further thoughts on what you did and
evaluate each stage of the project process.*

I chose this project because of a conversation my father had with the grower we buy Alphonso from
every summer. He had hired eleven pickers for a harvest he thought would need six and paid them all
for a day of standing about. His only way of estimating his crop was to walk the rows and look at
it. I wanted to know whether that number could come from a phone instead of from experience.

What I have so far is an estimator that works on simulated trees and works best where the problem is
hardest, on dense canopies scanned from only two or three positions. Three viewpoints with it are
more accurate than twelve without, which for a grower with two hundred trees is the difference
between a morning and a day. What it has not yet done is count a single real mango. Everything in
this report is measured on trees I generated, and I would rather say that plainly than let a reader
assume otherwise.

The part of the project I am most pleased with is not a result. Twice my own measurements
contradicted what I had set out to show. The first time, correcting the physics of my simulator
revealed that walking a full circle around a tree already recovers most of what one view hides, which
undercut the premise I had started from. The second time, comparing my trees against somebody else's
harvested orchard showed that mine were far too easy, because they had no trunks or branches in them
at all. Both times the right move was to change the claim rather than the code, and learning to do
that is worth more to me than the accuracy figure.

Working without a mentor cost me on both occasions. My simulator and my checks shared the same
assumptions, so everything agreed with itself and nothing caught the error. What eventually played
the sceptic was published field data from an orchard someone else had harvested, which is a poor
substitute for a person who is allowed to doubt you early.

The next stage is the one that decides whether any of this is true. Between February and May 2027 I
will scan real Alphonso trees, record a prediction and an interval before touching the fruit, and
then pick each tree and count every mango on it. That is the only ground truth that settles the
question, and it will either confirm the method or show me where it breaks.

## My mentor or supervisor

*If you had a project mentor or placement supervisor, how did they help with your project? Please
leave blank if you did not have one.*

-

*Ask your mentor to confirm that this project is your work by signing below.*

**Signature of mentor or supervisor:**

**Date:**

## Space for further notes / drawings / reflections (optional)

**Status of this submission.** The project is at its simulation stage. The estimator, the simulator
that tests it and the comparison against current practice are complete, and every number comes from
one seeded script. The orchard validation runs between February and May 2027, because the ground
truth for a tree is obtained by picking it and counting, and the fruit does not exist before then.

**Reproducing the work.** Everything in the report can be re-run. Two commands regenerate every
number and redraw every figure from a fixed seed, and a test suite of twenty tests checks the
simulator against closed-form answers rather than against itself. *The repository must be made
public before this is submitted.*

**How I used AI.** My use of AI is declared in full in the report, under "A note on AI use". In
short, I used Anthropic's Claude substantially rather than incidentally: it wrote most of the code
from my direction, drafted sections of the report from my decisions about what it should argue,
found several of the defects in the fix log, and proposed the parametric bootstrap that replaced my
first attempt at prediction intervals. I set the aim and the success conditions before any code
existed and held to them when the results contradicted what I expected, I decided to narrow the aim
rather than adjust the simulator, and I decided to stop tuning toward the published figure rather
than force agreement with it. The commit history holds the dated trail.

**What I cannot yet defend.** There are parts of this report I could not currently explain to an
assessor in conversation without preparation, particularly the zero-truncated likelihood and the
reasoning behind the parametric bootstrap. Those need studying until I can, or removing. I would
rather record that here than be found out in the interview.
"""


def main():
    data = json.loads(ROWS.read_text(encoding="utf-8"))
    OUT.write_text(PREAMBLE + build_table(data) + TAIL, encoding="utf-8")
    print(f"wrote {OUT.name}: {len(data['rows'])} criteria rows")


if __name__ == "__main__":
    main()
