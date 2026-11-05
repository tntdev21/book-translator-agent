# Technical & Non-Fiction — Category Card
**EN → VI guide for IT/technology, business/finance, science/medicine, self-help/psychology. Full research version: `technical.full.md`.**

## What This Category Is
- Terminology precision > stylistic freedom (10–30% of text is terms); one wrong term is a trust/safety failure. Cross-chapter consistency is mission-critical; clarity never at the cost of precision.

## Tone & Voice by Domain
| Domain | Register | Reader address | Pattern |
|---|---|---|---|
| IT/tech | formal + practical, minimal colloquialism | imperative (omit subject) or `Hãy…`; `bạn` acceptable | `Để cài đặt phần mềm, hãy làm theo các bước sau…` |
| Business/finance | formal + credible, professional distance | `bạn`; firm "we" → `chúng tôi` | `Chúng tôi khuyến nghị đầu tư vào…` |
| Science/medicine | formal + precise, evidence-based | impersonal (no subject) | `Phản ứng enzym xảy ra với tốc độ…` |
| Self-help | formal + warm, actionable | `bạn`, `Hãy thử…`, rhetorical question OK | `Bạn hoàn toàn có khả năng thay đổi…` |
| Academic | impersonal | `Có thể cải thiện… bằng cách…` (no `bạn`) | |

- Pronouns: professional audience `quý vị` (high formality); third parties `họ`/`anh ta`/`cô ta` keep source distance; authority figures in examples `ông`/`bà`.
- Do not render every "you" as `bạn` in formal tech context; prefer imperative or impersonal.
- One formality level per section; no oscillation between casual and technical. Northern standard VI for technical text.
- Too casual loses authority: `Chỉ cần bấm cái nút này là xong` ✗ → `Nhấp vào nút này để hoàn tất quá trình` ✓.
- Actionability: match verb strength to the source — "You should try" `Hãy thử` (high); "It's recommended" `Bạn nên`; "Consider" `Hãy cân nhắc`; "You might want to" `Bạn có thể`. Soft language stays soft where trade-offs exist.

## Terminology: Keep English vs Translate
**Keep English** when: universally recognised acronym (HTTP, API, SQL, JSON, AI, ML); brand/language/product name (Python, Azure); no settled VI equivalent; or target professionals use the English form. Heuristic: keep EN only if the term recurs (5+), VI would be longer/awkward, and the audience uses EN.
**Translate** when VI is shorter/natural (`nhà khoa học`, `chuyên gia`), the concept is culture/law-specific (`tuân thủ`), or readers are general (self-help translates more; IT reference keeps more).
- **Choose ONE form per term and lock it** (glossary); never alternate `cơ sở dữ liệu` / `database` / `DB` across chapters.
- Hybrid first mention: `cơ sở dữ liệu (database)`, then VI only. `phản vật chất (antimatter)` → `phản vật chất`.
- Ambiguous terms: resolve by context, glossary carries the sense — performance (system) `hiệu suất` / (person) `thành tích` / (show) `biểu diễn`.
- **Don't over-translate settled technical loans**: `JWT tokens` stays (first mention may gloss `(mã thông báo JSON Web Token)`), `connection pooling` may stay. **Don't translate word-for-word**: "separate concerns" → `phân chia trách nhiệm rõ ràng`, not `tách rời mối quan tâm`.

### Acronym tiers
1. Keep + VI gloss first use only: `API (Giao diện lập trình ứng dụng)`, `UI`, `UX`.
2. Keep acronym + translated expansion (new to VN market): `CRUD (Tạo/Đọc/Cập nhật/Xóa)`, `SDLC (Vòng đời phát triển phần mềm)`, `ROI` → `Lợi suất đầu tư (ROI)`.
3. Translate only (descriptive): End-to-End `từ đầu đến cuối`, state of the art `tiên tiến, hiện đại nhất`, best practice `thực tiễn tốt nhất`.
After the first mention, use one form consistently (acronym or VI, never both at random). REST stays `REST`.

### Base glossary
server `máy chủ` · client `client`/`máy khách` · function `hàm` · variable `biến` · loop `vòng lặp` · condition `điều kiện` · algorithm `thuật toán` · optimization `tối ưu hóa` · debugging `gỡ lỗi` · deployment `triển khai` · performance `hiệu suất` · upload `tải lên` · download `tải xuống` · button `nút` · menu `menu`/`trình đơn` · index `chỉ mục (index)` · Machine Learning `Học máy` (never `Máy học`).

## Structure Patterns
- **Steps**: numbered, imperative verb first, no subject (`Nhấp`, not `Bạn nhấp`), not `bạn nên`; one tense; split long steps; UI elements bold + quoted label (`Nhấp vào nút **Nhập**`). Optional `Bước N:` in ordered process lists.
- **Definitions**: tech docs lead with term + definition (`Điện toán đám mây là…`); accessible books may lead with the familiar concept then introduce the term; complex definitions may use explanatory footnote `(1)`.
- **Examples**: open with `Ví dụ,`; same list style as source; terms in parentheses on first mention; active voice.
- **Definition lists**: `Thuật ngữ: giải thích.`
- **Code references in prose**: `Sử dụng hàm getUserData() để…`; parameter names quoted unchanged (`Tham số 'timeout' chỉ định…`); error messages translated (`Kết nối bị từ chối: Máy chủ không phản hồi`).

## Code, Figures, Tables, Citations
- Code: unchanged; variable/function names English; comments may be translated; surrounding prose VI.
- Figures: `Hình X` (not "Diagram"); caption translated; diagram labels translated where possible.
- Tables: headers translated; data (numbers, acronyms) unchanged.
- Citations `[1]`: structure unchanged, author names unchanged; explanatory footnotes `(1)` translated. Keep the numbering scheme consistent.

## Domain Notes
- **Business**: keep instruments/acronyms (S&P, NYSE, ETF, GAAP); translate strategic concepts with explanation; note where VN regulation/currency differs (USD→VND only as a rate note where the book's style guide allows).
- **Science/medicine**: keep international scientific names with VI definition; dual reference for conditions (`Tăng huyết áp (cao huyết áp)`); dosage format `500mg hai lần mỗi ngày`; flag drug/regulatory terms for expert check.
- **Self-help**: familiar language for psychological concepts, no dumbing down.
- **Localisation**: adapt culture-bound comparisons only when the book's style guide permits (e.g. US tax return → `quyết toán thuế`); never change facts or figures.

## QA Checklist (per chunk)
- Glossary terms consistent; no random English mixed in; no variant renderings within a section.
- Formality consistent with domain; no casual/formal oscillation.
- No ambiguous pronouns; steps/lists preserved; numbers correct; code unchanged; table headers translated; footnotes/references intact.

