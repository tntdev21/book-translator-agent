# Giới thiệu
Tôi thích đọc tiểu thuyết trinh thám và các sách về lịch sử, văn hoá, khoa học…

Khi tác giả tôi yêu thích ra 1 cuốn mới bằng tiếng nước ngoài tôi không đọc được. Nhà xuất bản trong nước thì hoặc là không/chưa có kế hoạch dịch và xuất bản trong nước, hoặc là sẽ phải chờ rất lâu để được cầm cuốn sách trên tay đọc. Nên tôi viết chương trình này, cho AI agent cố gắng giả lập việc dịch sách với chất lượng gần với bản dịch của nhà xuất bản nhất, để tôi có thể thưởng thức tác phẩm cùng thời gian với các độc giả khác trên thế giới trong khi chờ được cầm cuốn sách trên tay.

# Ý tưởng thực hiện

## Kiến trúc 3 tầng

Để việc dịch được nhất quán, tôi chia “tri thức nền” thành 3 tầng
- Tầng 1 - tầng lõi: Bao gồm các nguyên tắc, nguyên lý, quy tắc, luật lệ, điều lệ, quy ước…chung bắt buộc phải tuân theo
- Tầng 2 - tầng thể loại: Bao gồm các thông tin đặc trưng của thể loại sách như tông giọng, cách hành văn, câu cú, độ dài đoạn, dòng, cách trình bày…
- Tầng 3 - tầng tác giả: Tương tự tầng 2 nhưng đây là các thông tin đặc trưng, mang dấu ấn riêng của tác giả

## Luồng công việc

Với mỗi sách cần dịch tôi cần phải xây dựng dữ liệu của tầng 3, nên tôi tạo một skill (kỹ năng) tên là `deriving-dna` định nghĩa các công việc cần làm để phục vụ tầng 3.

Sau đấy tôi viết một script để export cuốn sách gốc về định dạng AI dễ đọc nhất là markdown. Tiếp đến là cắt cuốn sách lớn thành nhiều khúc nhỏ để sau này nhiều agent có thể dịch song song đồng thời tối ưu hóa chi phí.

Trước khi bắt đầu dịch, sẽ có một danh sách check list cần kiểm tra để xem đã chuẩn bị sẵn sàng tài liệu để dịch chưa: file thông tin sách `book.yaml`, dữ liệu tầng 3 `dna.md`, style guide, bảng thuật ngữ, đánh dấu các trang đầu sách (trang tên sách, bản quyền, lời đề tặng…) và kiểm tra mục lục.

## 3 vai trò mô phỏng thế giới thực

Tôi tạo ra 2 agent tên là `translator` và `editor` có hai kỹ năng tương ứng `translating` và `editing`.  Ngoài ra mỗi phiên làm việc thì có một agent chính - quản lý, được nạp skill `book-translating` để điều phối công việc. Như vậy có 3 vai trò: 1 quản lý, nhiều dịch giả và 1 biên tập viên.

Quản lý sẽ cho 5 `translator` dịch song song 5 khúc (gọi là 1 lô). Khi cả 5 xong việc, quản lý sẽ chuyển cả lô cho 1 `editor` duy nhất rà soát lại bản dịch so với bản gốc. Khúc nào đạt thì cho qua, khúc nào có lỗi thì trả lại đúng `translator` đã dịch khúc đó để sửa, sửa xong lại quay về đúng `editor` đó duyệt lại, cho đến khi đạt chất lượng yêu cầu.

## Agent tự học hỏi và tiến bộ sau mỗi lần gặp lỗi

Khi `editor` tìm ra được lỗi, thì lỗi này sẽ được lưu vào kho tri thức, để lần tiếp theo `translator` không gặp lại tương tự. 

## Xuất ra bản mềm

Sau khi dịch xong, tôi viết 1 script để xuất bản thành file pdf, epub, html để dễ đọc trên các thiết bị điện tử.

## Điểm hay của pipeline

- **Làm việc như nhà xuất bản thật**: quản lý không được tự tay sửa bản dịch, mọi chỉnh sửa phải đuợc chính `translator` đã dịch khúc đó thực hiện. `editor` chỉ được tự sửa những lỗi gõ chắc chắn sai, còn dịch sai, lệch thuật ngữ, câu văn chưa mượt thì phải ghi nhận và trả lại cho `translator`. Khúc bị trả về phải được duyệt lại thêm 1 lần nữa.
- **Thuật ngữ nhất quán từ đầu đến cuối sách**: thuật ngữ mới được ghi vào sổ, tự chống trùng lặp. Một script lập bản đồ “thuật ngữ này đang được dịch thế nào ở khúc nào” và đánh dấu những chỗ cùng một từ mà bị dịch nhiều kiểu khác nhau.
- **Tri thức có thứ tự ưu tiên rõ ràng**: ngoài 3 tầng ở trên còn có style guide, bảng thuật ngữ, quy tắc trình bày và  danh sách lỗi do `editor` rút ra. Tất cả được gom lại thành một bản tóm tắt gọn riêng cho từng vai trò, để agent đọc nhanh và tốn ít token.
- **Tối ưu chi phí**: tận dụng prompt caching, sau mỗi lô có bảng báo cáo token, cache và chi phí $ của từng agent, kèm chi phí trung bình cho mỗi khúc.
- **Lưu trạng thái**: mỗi khúc có trạng thái riêng (`pending → translated → review → rework → qa_passed`), nếu tắt máy đi ngủ, hôm sau chạy lại là pipeline tự biết để tiếp tục công việc.
- **Đầu vào, đầu ra đa dạng**: nhận sách gốc dạng PDF, DOCX, EPUB, TXT. Xuất ra PDF, EPUB, HTML có mục lục tự động, ảnh bìa và nhúng sẵn font Literata.
- **Tự sửa lỗi định dạng**: Trước khi xuất bản, hệ thống tự phát hiện chữ Trung, Nhật lọt vào bản dịch, chữ bị dính nhau, nối lại câu bị ngắt dòng, chuẩn hoá dấu gạch ngang, viết hoa tên riêng.

# Thực hiện

## Kiến trúc 3 tầng
- Tầng 1 tôi không biết làm nên tôi nói AI đi research và làm cho tôi.
- Tầng 2 cũng thế :D
- Tầng 3 thì tôi dùng bản gốc tiếng nước ngoài và bản dịch đã xuất bản ở Việt Nam của cùng tác giả, cho AI đọc đối chiếu và xây dựng dữ liệu.

## Code

Tôi không code dòng nào hết vì tôi biết AI code tốt hơn tôi. Tôi chỉ nói chuyện với AI để làm rõ ý tưởng, nhu cầu của mình, định hướng luồng công việc sao cho nhanh, hiệu quả và chất lượng.  Cuối cùng tôi xác thực chất lượng đầu ra.

# Kết quả

Sau 30 phút ngồi chờ ở sân bay, vibe coding sản phẩm này, cùng với một tuần làm việc liên tục thì xong sản phẩm.

Tôi cho dịch thử một cuốn sách dài 210.000 từ. Thời gian Agent chạy là 2 tiếng, đốt hết lượng token tương đương tầm 5$ trong quota của gói subscription. Nếu trả theo giá API thì chi phí cao hơn, khoảng 0,8$ cho mỗi khúc ~3.000 từ (đo bằng model sonnet 5.5).

Nếu bạn không biết code, không sao, cứ đưa link repo này cho AI agent của bạn, nó sẽ tự biết phải phục vụ bạn như thế nào (tài liệu dành cho agent: [`README-FOR-AGENTS.md`](README-FOR-AGENTS.md)).

# Tuyên bố miễn trừ trách nhiệm

Tôi làm sản phẩm này phục vụ nhu cầu cá nhân, source code này tôi chia sẻ để người đọc tham khảo, học hỏi. Tôi không chịu trách nhiệm với bất kỳ hệ quả nào từ việc người đọc sử dụng mã nguồn này ngoài mục đích trên. 

# Giấy phép

Mã nguồn được công khai để tham khảo (source-available), **không phải open source**. Phát hành theo giấy phép [PolyForm Noncommercial 1.0.0](LICENSE): được dùng cho mục đích cá nhân, học tập, nghiên cứu và các mục đích phi thương mại khác; không được dùng cho mục đích thương mại.

Chỉ dịch những cuốn sách bạn có quyền dịch. Không đưa nội dung sách gốc hay bản dịch có bản quyền lên bản fork công khai.
