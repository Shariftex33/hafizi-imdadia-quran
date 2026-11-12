# Hafizi Imdadia Quran (15 lines) – text version

A text (not scanned) version of the 15-line Hafezi Quran of Emdadia Library, Bangladesh.
Every page has the same lines as the print: each line starts and ends on the same word.

Open `index.html` in a browser. Nothing needs to be installed.

## What is in it

- All 610 pages, 15 lines each, with the print's page breaks and line breaks.
- The two opening pages (Fatiha, start of Baqarah): heading, bismillah line and 7 lines.
- Surah headings with ayat and ruku counts, ruku marks, sajdah marks, waqf signs.
- Juz start (heavier, larger first line) and the quarter, half and three-quarter marks of each juz in the margin.
- Mutashabihat (repeated phrases) in colour, with cross-references in the margin.
- Tap a word for its meaning, or an ayah circle for the translation of the ayah (English: Saheeh International; Bangla: Muhiuddin Khan).
- Font: Al Qalam Quran Majeed 4. Another font can be chosen or uploaded from the toolbar.

Page numbers: the box in the toolbar counts from 1; the number printed in the page header is one higher, as in the print.

## Files

| Path | Content |
| --- | --- |
| `index.html` | the app |
| `data/pages.js` | Quran text and waqf signs (Indo-Pak script) |
| `data/imdadia_lines.js` | the line structure read from the print |
| `data/imdadia_fixes.js` | manual corrections to that structure, made page by page against the print |
| `data/imdadia_marks.js` | quarter / half / three-quarter marks of each juz |
| `data/hafizi_imdadia_structure_final.csv` | the final structure: one row per printed line with its first word, last word and all words |
| `data/hafizi_imdadia_structure_final.js` | the same final structure for programs |
| `data/tr_*.js`, `data/wbw_*.js`, `data/fn_*.js` | translations, word meanings, footnotes |
| `fonts/` | fonts used by the app |
| `tools/` | the scripts that read the line structure from the scan and build the app (kept for reference; they expect the original working folder) |

## How the line structure was made

Each ruled line of the scanned print was read by OCR, and the known Quran text was cut into those lines
so that every line matches what was read there. Only the positions of the line breaks come from the scan;
the text itself always comes from `data/pages.js`. All pages flagged as uncertain were then checked by eye
against the print and corrected.

Known limits: the three-quarter marks of juz 10, 17 and 19 use the standard positions because they were not
found in the scan; where the print leaves a lone "و" at the end of a line, the app keeps it with its word on the next line.

## Sources

- Text and waqf signs: Quranic Universal Library (QUL), Indo-Pak script.
- Translations: English – Saheeh International (QuranEnc.com); Bangla – Maulana Muhiuddin Khan, from Tanzil.net (tanzil.net/trans, text unchanged).
- Word meanings: English – Quran.com; Bangla – Greentech Apps Foundation / QuranWBW.
- Line structure: Hafezi Quran, Emdadia Library (15 lines).
