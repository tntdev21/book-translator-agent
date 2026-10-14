# Technical & Non-Fiction Translation Patterns
## English → Vietnamese Guide

**Version**: 1.0
**Created**: 2025-12-04
**Research Date Range**: 2024-2025
**Domain Focus**: Technology, Business, Science, Self-help, Medicine

---

## Executive Summary

Technical/non-fiction translation presents distinct challenges compared to narrative genres:
- **Terminology precision** outweighs stylistic freedom
- **Consistency** across documents, glossaries, and termbases is mission-critical
- **Reader trust** depends on accurate technical information
- **Clarity** must never sacrifice precision
- **Localization** requires domain expertise plus cultural adaptation

Key differentiator: 10-30% of technical text is specialized terminology requiring careful research and standardization. Poor terminology choices can cascade into compliance failures, product recalls, or patent rejections.

---

## 1. Tone & Voice Framework

### 1.1 Formality Levels by Domain

**IT/Technology** (Formal + Practical)
- Objective, technical precision required
- Direct instruction style
- Minimal colloquialisms
- Professional vocabulary but accessible language
- Example: "Để cài đặt phần mềm, hãy làm theo các bước sau..." (neutral, instructional)

**Business/Finance** (Formal + Credible)
- Authority establishment essential
- Trust-building language
- Professional distance maintained
- Complex concepts simplified without losing accuracy
- Example: "Chiến lược tài chính này giúp giảm rủi ro..." (authoritative, credible)

**Science/Medicine** (Formal + Precise)
- Accuracy over accessibility (readers are domain experts)
- Technical terminology unavoidable
- Objective narration throughout
- Evidence-based claims emphasized
- Example: "Phản ứng enzym xảy ra với tốc độ..." (precise, technical)

**Self-help/Psychology** (Formal + Warm)
- Approachable formality (not cold)
- Personal relevance emphasized
- Practical actionability throughout
- Second-person engagement
- Example: "Để cải thiện tâm lý của bạn, bạn nên..." (warm, practical)

### 1.2 Vietnamese Pronoun System for Technical Contexts

**Critical Rule**: Vietnamese pronoun choice signals relationship & respect

| Context | Pronoun | Usage | Notes |
|---------|---------|-------|-------|
| Author → Reader (instructional) | "bạn" or omit | "Bạn cần..." or "Hãy..." | Neutral, practical |
| Author → Professional audience | "quý vị" | "Quý vị nên biết rằng..." | High formality |
| Describing third parties | "họ" / "cô ta" / "anh ta" | Depends on familiarity | Maintain original distance |
| Addressing authority figures | "ông" / "bà" | In dialogue/examples | Show respect |
| Instructions (imperative) | Omit subject | "Nhấp vào nút..." | Most natural in tech docs |

**Mistake to avoid**: Direct "you" translation ("Bạn có thể giúp tôi không?") sounds unnatural in formal tech contexts. Better: "Có thể giúp được" or "Hãy giúp tôi".

### 1.3 Tone Consistency Across Chapters

- **Maintain formality level** consistently within document section
- **Don't oscillate** between casual dialogue and technical exposition
- **Regional dialect**: Use Northern Vietnamese (standard) for formal/technical; Southern acceptable for narrative parts but not technical
- **Voice stability**: Same terminology source = same voice authority

---

## 2. Terminology Management Strategy

### 2.1 The Terminology Challenge in Numbers

- **Coverage**: 10-30% of technical text consists of specialized terms
- **Machine translation error rate**: ~50% for acronyms in Google Translate
- **Consistency cost**: Single inconsistent term = rework across entire document
- **Risk level**: Misplaced medical/engineering term = safety liability

### 2.2 When to Keep English (Untranslated)

**Keep English for:**
1. **Universally recognized technical acronyms**
   - HTTP, USB, API, SQL, JSON, AWS, IoT, AI, ML
   - Reason: Vietnamese tech professionals use these terms; translation confuses
   - Format: Keep + add Vietnamese explanation on first use only
   - Example: "API (Giao diện lập trình ứng dụng) cho phép..."

2. **Proprietary/Brand names**
   - JavaScript, Python, Java, Microsoft, Google, Azure
   - Reason: Trademark & industry standard
   - Never translate

3. **No established Vietnamese equivalent**
   - "bandwidth" → "băng thông" (newer term, used as-is)
   - "cloud computing" → "điện toán đám mây" (longer phrase than English)
   - Solution: Keep English + definition or use descriptive Vietnamese

4. **Already commonly used by target professionals**
   - "database" → some docs use "database", others use "cơ sở dữ liệu"
   - Consistency within **your glossary** matters more than universal standard
   - Example: Choose ONE form in glossary, use consistently

**Keep English ONLY if**:
- Term appears 5+ times in document
- Vietnamese equivalent would be longer/awkward
- Target audience (Vietnamese tech professionals) uses English form

### 2.3 When to Translate

**Translate when:**
1. **Vietnamese equivalent is shorter/more natural**
   - "scientist" → "nhà khoa học" (shorter, natural)
   - "expert" → "chuyên gia" (clear, common)

2. **Concept is culturally specific to English-speaking context**
   - "regulation" → needs context-specific translation per Vietnamese law
   - "compliance" → "tuân thủ" or "tuân theo" (depends on domain)

3. **Target readers are general audience, not specialists**
   - Self-help: translate more
   - IT reference docs: keep more English

4. **Building terminology creates consistency**
   - First occurrence: define both English + Vietnamese
   - Subsequent: use Vietnamese form consistently
   - Example: "phản vật chất (antimatter)" first use; then "phản vật chất" thereafter

### 2.4 Acronym Translation Rules

**Three-tier approach:**

**Tier 1: Never translate** (universally recognized)
```
API → API (Giao diện lập trình ứng dụng)
UI → UI (Giao diện người dùng) - first use only
UX → UX (Trải nghiệm người dùng)
```

**Tier 2: Translate + keep acronym** (new to Vietnamese market)
```
CRUD → CRUD (Tạo/Đọc/Cập nhật/Xóa)
SDLC → SDLC (Vòng đời phát triển phần mềm)
```

**Tier 3: Translate only** (descriptive, no acronym in Vietnamese)
```
End-to-End → từ đầu đến cuối
State of the art → tiên tiến, hiện đại nhất
Best practice → thực tiễn tốt nhất
```

**Implementation**:
1. Create glossary entry with Vietnamese + English form
2. First mention: "API (Giao diện lập trình ứng dụng)"
3. Subsequent: use consistently (either API or Vietnamese, but not both randomly)

---

## 3. Structure Conventions for Technical Content

### 3.1 Step-by-Step Instructions Pattern

**English pattern**:
```
1. Open the file dialog
2. Select the document
3. Click Import
4. Wait for processing
5. Confirm completion
```

**Vietnamese translation pattern**:
```
1. Mở hộp thoại tập tin
2. Chọn tài liệu
3. Nhấp vào "Nhập"
4. Chờ quá trình xử lý hoàn tất
5. Xác nhận hoàn thành
```

**Rules**:
- Use imperative form (command), not "bạn nên" (you should)
- Omit subject: "Nhấp" not "Bạn nhấp"
- Number format: "1." followed by action verb
- Action verb at start (maximize clarity scanning)
- Keep tense consistent (simple present)

**Clarity techniques**:
- Split long steps into sub-steps
- Add visual cues: "Bạn sẽ thấy..." (You will see...)
- Use bold for UI elements: Click **Import button**
- Example: "Nhấp vào nút **Nhập**. Cửa sổ mới xuất hiện." (Split for clarity)

### 3.2 Definition & Explanation Pattern

**English**: "Cloud computing is the delivery of IT services over the internet..."

**Vietnamese options**:

**Option A: Lead with term + definition**
```
Điện toán đám mây là cung cấp dịch vụ CNTT qua internet...
```

**Option B: Lead with familiar concept, then introduce term**
```
Thay vì lưu trữ dữ liệu trên máy tính cá nhân, bạn có thể sử dụng
"điện toán đám mây" - dịch vụ lưu trữ qua internet...
```

**Option C: Use footnote for complex definitions**
```
Điện toán đám mây(1) cung cấp dịch vụ CNTT qua internet.

(1) Điện toán đám mây: Cung cấp tài nguyên máy tính (máy chủ,
    lưu trữ, phần mềm) qua mạng internet thay vì máy tính cá nhân.
```

**Best practice**: Use Option B for self-help/business documents (accessible). Use Option A for tech docs (assumes domain knowledge).

### 3.3 Examples & Case Studies Pattern

**English pattern**:
```
For example, if you want to optimize your database, consider:
- Adding indexes to frequently queried columns
- Removing redundant data
- Using connection pooling
```

**Vietnamese pattern**:
```
Ví dụ, nếu bạn muốn tối ưu hóa cơ sở dữ liệu, hãy cân nhắc:
- Thêm chỉ mục (index) vào các cột được truy vấn thường xuyên
- Xóa dữ liệu dư thừa
- Sử dụng connection pooling
```

**Rules**:
- "Ví dụ" (for example) at start
- List format consistent with instructions (bullet or number)
- Technical terms in parentheses on first mention
- Active voice preferred

### 3.4 Lists & Enumerations Pattern

**Ordered list** (step-by-step process):
```
1. Bước 1: Khởi động ứng dụng
2. Bước 2: Đăng nhập
3. Bước 3: Chọn tính năng
```

**Unordered list** (options, advantages, considerations):
```
Lợi ích của sử dụng API:
- Tiết kiệm thời gian phát triển
- Tập trung vào logic kinh doanh
- Có thể tái sử dụng
```

**Definition list** (term + explanation):
```
Cơ sở dữ liệu: Tập hợp dữ liệu được tổ chức và lưu trữ.
API: Giao diện cho phép các ứng dụng giao tiếp với nhau.
```

---

## 4. Domain-Specific Patterns

### 4.1 Technology/IT Domain

**Terminology approach**:
- Keep acronyms (API, JSON, SQL)
- Translate processes ("upload" → "tải lên", "download" → "tải xuống")
- Translate UI elements ("button" → "nút", "menu" → "menu" or "trình đơn")
- Hybrid terms: "database" → "cơ sở dữ liệu (database)" on first use, then "cơ sở dữ liệu"

**Tone markers**:
- Objective, instructional
- Precision over elegance
- Second-person engagement: "Bạn có thể..." or imperative: "Hãy..."
- Example: "Hãy kiểm tra lỗi này trước khi triển khai" (Check this error before deploying)

**Common patterns**:
```
Error message format:
EN: "Connection refused: The server is not responding"
VI: "Kết nối bị từ chối: Máy chủ không phản hồi"

Code reference:
EN: "Use the getUserData() function to retrieve user information"
VI: "Sử dụng hàm getUserData() để lấy thông tin người dùng"

Parameter description:
EN: "The 'timeout' parameter specifies seconds to wait"
VI: "Tham số 'timeout' chỉ định số giây cần chờ"
```

**Vietnamese tech glossary base**:
| English | Vietnamese | Notes |
|---------|------------|-------|
| server | máy chủ | Keep Vietnamese |
| client | client / máy khách | Hybrid acceptable |
| function | hàm | |
| variable | biến | |
| loop | vòng lặp | |
| condition | điều kiện | |
| algorithm | thuật toán | |
| optimization | tối ưu hóa | |
| debugging | gỡ lỗi | |
| deployment | triển khai | |
| performance | hiệu suất | |

### 4.2 Business/Finance Domain

**Terminology approach**:
- Translate key terms (adds local relevance)
- Keep financial instruments/acronyms (S&P, NYSE, ETF)
- Translate strategic concepts with explanations
- Adapt to Vietnamese business context (tax codes, regulations differ)

**Tone markers**:
- Authoritative, credible
- Build trust through precise language
- Professional distance: "Các chuyên gia..." (Experts suggest...)
- Example: "Chiến lược này giúp giảm rủi ro 40% theo nghiên cứu của Goldman Sachs"

**Common patterns**:
```
Recommendation format:
EN: "We recommend investing in growth stocks during market upturns"
VI: "Chúng tôi khuyến nghị đầu tư vào cổ phiếu tăng trưởng trong những giai đoạn
     thị trường lên"

Financial metric:
EN: "The ROI for this investment is 15% annually"
VI: "Lợi suất đầu tư (ROI) của khoản đầu tư này là 15% hàng năm"

Regulatory reference:
EN: "Under GAAP standards, you must disclose..."
VI: "Theo tiêu chuẩn GAAP, bạn phải công khai..."
```

**Localization requirements**:
- Currency conversion (USD → VND with current rate note)
- Regulatory context (US law → Vietnamese law equivalent)
- Market references (S&P 500 → HSX equivalent)

### 4.3 Science/Medicine Domain

**Terminology approach**:
- Keep international scientific terms (with Vietnamese definition)
- Translate medical conditions into patient-friendly language
- Preserve technical names in parentheses for professional readers
- Use footnotes for complex explanations

**Tone markers**:
- Objective, evidence-based
- Technical vocabulary unavoidable
- Credibility through precision
- Example: "Phản ứng enzym xảy ra với tốc độ Michaelis-Menten..."

**Common patterns**:
```
Medical condition (dual reference):
EN: "Hypertension (high blood pressure) affects 30% of adults"
VI: "Tăng huyết áp (cao huyết áp) ảnh hưởng đến 30% người lớn"

Scientific process:
EN: "DNA replication occurs through semi-conservative mechanism"
VI: "Sao chép DNA xảy ra thông qua cơ chế bán bảo tồn"

Dosage/measurement:
EN: "Take 500mg twice daily"
VI: "Uống 500mg hai lần mỗi ngày"
```

**Terminology caveat**:
- Medical translation often requires local medical consultant
- Vietnamese health regulations differ from English-speaking countries
- Drug names may differ by region

### 4.4 Self-Help/Psychology Domain

**Terminology approach**:
- Translate psychological concepts (builds accessibility)
- Use familiar language over academic terminology
- Explain theories without dumbing down
- Localize examples to Vietnamese context

**Tone markers**:
- Warm, supportive, practical
- Second-person engagement: "Bạn có thể..." (You can...)
- Action-oriented: "Hãy thử..." (Try...)
- Hope/empowerment emphasized
- Example: "Bạn hoàn toàn có khả năng thay đổi tư duy này"

**Common patterns**:
```
Emotional validation:
EN: "It's normal to feel anxious when starting something new"
VI: "Bạn cảm thấy lo lắng khi bắt đầu điều gì đó mới là hoàn toàn bình thường"

Action step:
EN: "Over the next week, practice noticing your thoughts"
VI: "Trong tuần tới, hãy thực hành chú ý đến suy nghĩ của bạn"

Research reference:
EN: "Studies show that meditation reduces stress by 40%"
VI: "Các nghiên cứu chỉ ra rằng thiền định giảm căng thẳng 40%"
```

**Localization priority**: Self-help = high localization. Examples must resonate with Vietnamese readers.

---

## 5. Formatting Conventions (Technical Content)

### 5.1 Code Blocks & Technical References

**Rule**: Keep code snippets in English (no translation)

```javascript
// English comment - keep as-is
function getUserData(userId) {
  return fetch(`/api/users/${userId}`)
    .then(response => response.json())
    .catch(error => console.error('Lỗi:', error));
}
```

**Surrounding text in Vietnamese**:
```
Ví dụ dưới đây lấy dữ liệu người dùng bằng ID:

[CODE BLOCK]

Hàm này sử dụng fetch() để kết nối đến API endpoint /api/users/{userId}.
```

**Rule**:
- Code: English (unchanged)
- Comments in code: Can translate to Vietnamese
- Surrounding narrative: Vietnamese
- Variable names: English (no translation)

### 5.2 Technical Diagrams & References

**English**: "See Figure 3 for the system architecture diagram"

**Vietnamese options**:

**Option A** (direct reference):
```
Xem Hình 3 để thấy sơ đồ kiến trúc hệ thống
```

**Option B** (descriptive):
```
Hình 3 cho thấy cách các thành phần của hệ thống kết nối với nhau
```

**Option C** (with explanation):
```
Sơ đồ kiến trúc (Hình 3) hiển thị: máy khách gửi yêu cầu → máy chủ xử lý
→ cơ sở dữ liệu lưu trữ
```

**Best practice**:
- Caption translated
- Diagram labels translated (if possible)
- Reference format: "Hình X" (not "Diagram X")

### 5.3 Tables & Chart Descriptions

**Column headers**: Translate to Vietnamese

**Data**: Keep as-is (numbers, acronyms)

**Example**:

| Phương pháp | Chi phí | Hiệu suất | Ưu điểm |
|-------------|--------|----------|---------|
| API REST | Thấp | 95% | Dễ triển khai |
| GraphQL | Trung bình | 98% | Linh hoạt |
| gRPC | Cao | 99.5% | Hiệu suất cao |

### 5.4 Footnotes & Citations

**Academic citation format**:
```
[1] Smith, J. (2023). "Cloud Computing Architecture."
    Journal of Computer Science, 45(3), 234-245.
```

**Explanation footnote**:
```
(1) Điện toán đám mây: Cung cấp tài nguyên máy tính qua mạng internet
    thay vì máy tính cục bộ.
```

**Numbering**:
- Use superscript [1], [2], [3] for citations
- Use (1), (2), (3) for explanatory footnotes
- Keep consistent throughout document

**Translation rule**:
- Citation structure unchanged
- Explanatory content translated
- Author names unchanged

---

## 6. Reader Engagement Techniques

### 6.1 Second-Person Usage ("You")

**English pattern**: "You can improve performance by..."

**Vietnamese patterns**:

**Option A: Direct "bạn" (most common in tech docs)**
```
Bạn có thể cải thiện hiệu suất bằng cách...
```

**Option B: Imperative (most natural in instructions)**
```
Hãy cải thiện hiệu suất bằng cách...
(Omit subject, use "hãy")
```

**Option C: Passive impersonal (formal/technical)**
```
Có thể cải thiện hiệu suất bằng cách...
(No subject, no "bạn")
```

**Option D: Rhetorical question (engagement heavy)**
```
Bạn muốn cải thiện hiệu suất? Hãy thử...
```

**Selection rule**:
- Tech docs: B (imperative) - most natural
- Self-help: A or D - personal, engaging
- Academic: C - impersonal, formal
- Business: A - professional but approachable

### 6.2 Actionable Language

**Weak**: "It might be beneficial to consider implementing..."

**Strong**: "Hãy triển khai tính năng này để tăng tốc độ 40%"

**Patterns for actionability**:

| English | Vietnamese | Energy |
|---------|------------|--------|
| You should try | Hãy thử | High |
| It's recommended to | Bạn nên | Medium |
| Consider doing | Hãy cân nhắc | Low |
| You might want to | Bạn có thể | Medium |

**Rule**: Use stronger verbs when impact/benefit is clear. Use softer language when trade-offs exist.

```
Weak actionable:
EN: "You might consider testing this before deploying"
VI: "Bạn có thể cân nhắc kiểm tra điều này trước khi triển khai"

Strong actionable (same meaning, more persuasive):
EN: "Test this thoroughly before deploying to prevent failures"
VI: "Hãy kiểm tra kỹ lưỡng trước khi triển khai để tránh lỗi"
```

### 6.3 Practical Examples (Vietnamese Localization)

**Error**: Using English-only examples

**Correct**: Localize examples to Vietnamese context

```
EN: "For example, if you're a US company using GDPR..."
VI: "Ví dụ, nếu bạn là một doanh nghiệp Việt Nam phải tuân thủ
     PDPA (Pháp lệnh Bảo vệ Dữ liệu Cá nhân Asean)..."

EN: "John spent $5000 on marketing"
VI: "John chi 120 triệu VND cho tiếp thị" (with rate note: 1 USD ~ 24,000 VND)

EN: "You save 3 hours weekly on administrative tasks"
VI: "Bạn tiết kiệm 3 giờ mỗi tuần cho các công việc hành chính"
```

---

## 7. Glossary & Terminology Consistency

### 7.1 Building Your Technical Glossary

**Structure**:
```
English Term | Vietnamese | Domain | First Mention | Notes
```

**Example entries**:
```
API | Giao diện lập trình ứng dụng | IT | Chapter 2 | Keep acronym on first use
Database | Cơ sở dữ liệu | IT | Chapter 1 | Consistent form only
Machine Learning | Học máy | AI | Chapter 5 | Do NOT use "Máy học"
```

**Process**:
1. Extract all terms from source document
2. Research Vietnamese equivalents (glossaries, industry standards, competitor translations)
3. Verify with Vietnamese speakers in domain
4. Test for consistency across 5+ occurrences
5. Lock glossary before translation starts
6. All translators use identical glossary

### 7.2 Term Variation Management

**Problem**: Multiple translations exist

```
"Machine Learning" could be:
- Học máy (academic, literal)
- Máy học (awkward)
- Máy học máy (worse)
- ML (keep English)
```

**Solution**:
1. Research published Vietnamese technical books on the topic
2. Check industry standards in Vietnam (if applicable)
3. Select ONE form
4. Add to glossary with rationale
5. Use exclusively

**Documented rationale example**:
```
Machine Learning → Học máy
Rationale: Standard translation used by VNU Computer Science Department
          and major Vietnamese tech publishers (O'Reilly Vietnamese,
          Toptal Vietnamese guide). More natural than "máy học".
```

### 7.3 Handling Ambiguous Terms

**Problem**: English term has 3+ Vietnamese meanings depending on context

```
"Performance" could mean:
- Hiệu suất (system performance - metrics)
- Thành tích (person's performance - results)
- Biểu diễn (performance - entertainment)
```

**Solution**: Add context to glossary

```
Performance (system/technical) | Hiệu suất | Describe how fast/efficiently a system operates
Performance (human/work) | Thành tích | Results, achievements, outcomes
```

**Usage rule**: Always check context before using glossary term.

### 7.4 Acronym Consistency Matrix

**Create table for all acronyms**:

| Acronym | Full Form EN | Vietnamese | Usage | First Mention |
|---------|--------------|-----------|-------|----------------|
| API | Application Programming Interface | Giao diện lập trình ứng dụng | Keep "API" + VI translation first use | Ch.2 |
| REST | Representational State Transfer | Keep "REST" | No translation needed | Ch.2 |
| CRUD | Create/Read/Update/Delete | Tạo/Đọc/Cập nhật/Xóa | Keep "CRUD" + VI first use | Ch.3 |

---

## 8. Common Translation Pitfalls & Solutions

### Pitfall 1: Over-translating Technical Terms

**❌ Wrong**:
```
"We recommend using JWT tokens for authentication"
VI: "Chúng tôi khuyến nghị sử dụng mã thông báo JWT để xác thực"
```

**✅ Correct**:
```
VI: "Chúng tôi khuyến nghị sử dụng JWT tokens để xác thực"
(or first mention: "JWT tokens (mã thông báo JSON Web Token)")
```

### Pitfall 2: Inconsistent Terminology Across Chapters

**❌ Wrong**:
```
Chapter 2: "Cơ sở dữ liệu SQL..."
Chapter 5: "Database quan hệ..."
Chapter 8: "DB có khóa ngoài..."
(Same concept, three different terms)
```

**✅ Correct**:
```
All chapters: "Cơ sở dữ liệu SQL" (locked form)
```

### Pitfall 3: Word-for-Word Translation of Technical Phrases

**❌ Wrong**:
```
EN: "Best practice is to separate concerns"
VI: "Thực tiễn tốt nhất là tách rời mối quan tâm"
(Literal, unnatural)
```

**✅ Correct**:
```
VI: "Thực tiễn tốt nhất là phân chia trách nhiệm rõ ràng"
(Meaning, more natural)
```

### Pitfall 4: Lost Cultural Context

**❌ Wrong**:
```
EN: "This is as easy as filing a tax return"
VI: "Cái này dễ như nộp tờ khai thuế"
(American context doesn't resonate)
```

**✅ Correct**:
```
VI: "Cái này dễ như nộp hồ sơ quyết toán thuế"
(Vietnamese tax filing reference)
```

### Pitfall 5: Forgetting Precision in Informal Contexts

**❌ Wrong** (too casual for technical docs):
```
"Chỉ cần bấm cái nút này là xong"
(Too informal, loses authority)
```

**✅ Correct**:
```
"Nhấp vào nút này để hoàn tất quá trình"
(Professional, clear)
```

---

## 9. Quality Assurance Checklist for Technical Translations

**Terminology**:
- [ ] All terms from glossary used consistently
- [ ] No untranslated English mixed randomly throughout
- [ ] Acronyms defined on first mention
- [ ] No term variations within same section

**Tone & Voice**:
- [ ] Formality level consistent with domain
- [ ] Instructional tone consistent
- [ ] No oscillation between formal/casual
- [ ] Reader trust maintained

**Clarity**:
- [ ] No ambiguous pronoun references
- [ ] Technical concepts clearly defined
- [ ] Examples support main points
- [ ] Structure (steps, lists) preserved

**Accuracy**:
- [ ] Numbers, measurements converted correctly
- [ ] Code blocks unchanged
- [ ] Technical facts verified
- [ ] No information added/removed

**Formatting**:
- [ ] Code/technical references unchanged
- [ ] Tables translated (headers)
- [ ] Footnotes accurate
- [ ] Links/references functional

**Localization**:
- [ ] Examples resonate with Vietnamese context
- [ ] Currency conversions included
- [ ] Regulatory differences noted
- [ ] Regional references appropriate

---

## 10. Research Sources & Standards

**Consulted Sources**:
- [Vietnamese-English Translation Practice](https://www.slideshare.net/slideshow/vietnamese-english-translation-practice-pdf/269290619)
- [Vietnamese Technical Translation - Globalization Partners](https://www.globalizationpartners.com/resources/vietnamese-technical-translation/)
- [Technical Terms Translation Guide - Centus](https://centus.com/blog/how-to-translate-technical-terms)
- [On Translating Technical Terminology - ACL Anthology](https://aclanthology.org/2024.amta-research.6/)
- [Vietnamese Translation Challenges - 1StopAsia](https://www.1stopasia.com/blog/top-5-challenges-in-vietnamese-translation-and-how-to-solve-them/)
- [Terminology Management - ATL Translate](https://www.atltranslate.com/blog/terminology-management)
- [Technical Documentation Best Practices - Smartling](https://www.smartling.com/blog/technical-documentation-translation)

**Standards Referenced**:
- GAAP (General Accepted Accounting Principles) - Business domain
- GDPR (General Data Protection Regulation) - Data protection reference
- PDPA (ASEAN Personal Data Protection Regulation) - Vietnamese legal standard

---

## 11. Unresolved Questions & Future Research

1. **Vietnamese technical terminology standardization**: What is the official standard body (if any) for Vietnamese IT/technical terminology? (Currently varies by publisher/university)

2. **Regional variation impact**: How much should Southern Vietnamese dialect variations affect technical translations? (Current guidance: use Northern standard, but real-world usage varies)

3. **Legacy term adoption**: When Vietnamese professionals use English terms (e.g., "machine learning" not "học máy"), should translations enforce the "correct" Vietnamese or match market practice?

4. **Medical/pharmaceutical term regulation**: Are there official Vietnamese government standards for medical terminology translations? (Likely, but requires regulatory research)

5. **Financial regulation localization**: How to handle finance/business terms when Vietnamese and English financial systems differ substantially? (Requires domain expert consultation per document)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-04
**Maintenance**: Review & update annually based on emerging terminology patterns

