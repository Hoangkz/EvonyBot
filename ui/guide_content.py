"""
guide_content.py — nội dung màn "Hướng dẫn" (HTML đơn giản cho QTextBrowser).

GUIDE là danh sách (tiêu đề, HTML) theo thứ tự hiện ở danh mục bên trái. Để sửa chữ chỉ cần sửa file này;
để thêm mục thì thêm một cặp vào cuối GUIDE. Nằm trong code (không phải file .md rời) để bản cài đặt luôn có đủ.
"""

GUIDE: list[tuple[str, str]] = [
    ("Bắt đầu nhanh", """
<h2>Bắt đầu nhanh</h2>
<ol>
  <li>Mở giả lập (MEmu...) và vào game Evony.</li>
  <li>Ở màn <b>Home</b>, bấm <b>Load Devices</b> để bot quét tìm các giả lập đang mở.</li>
  <li>Bấm tên giả lập ở thanh bên trái để mở màn cấu hình của nó.</li>
  <li>Tích các việc muốn bot làm ở từng tab, rồi sang tab <b>Initialization</b> bấm <b>Start</b>.</li>
  <li>Xem bot đang làm gì ở tab <b>Logs</b>.</li>
</ol>
<p>Muốn chạy nhiều giả lập cùng lúc: cấu hình xong từng máy rồi bấm <b>Start All</b> ở Home.</p>
"""),
    ("Màn Home", """
<h2>Màn Home</h2>
<p>Màn đầu tiên khi mở app, hiện danh sách các giả lập và việc mỗi máy đang làm.</p>
<ul>
  <li><b>Load Devices</b>: quét các cổng ADB trong khoảng <i>Start port</i> – <i>End port</i> để tìm giả lập.</li>
  <li><b>Active / Inactive</b>: máy Inactive sẽ bị bỏ qua khi bấm Start All.</li>
  <li><b>Start All / Stop All</b>: chạy / dừng bot trên mọi máy.</li>
  <li><b>Exit All</b>: đóng game trên mọi máy.</li>
  <li><b>Server reset time</b>: giờ reset hằng ngày của server, dùng chung cho mọi máy.</li>
  <li><b>Auto Times Out</b>: sau số phút này bot đóng game để nghỉ.</li>
  <li>Cập nhật: app tự kiểm tra bản mới; có thể kiểm tra thủ công ngay ở màn này.</li>
</ul>
<p>Thêm máy thủ công: bấm <b>＋ Add device</b> ở thanh bên rồi nhập cổng (VD <code>21513</code>).</p>
"""),
    ("Initialization", """
<h2>Initialization</h2>
<p>Tab điều khiển chính của mỗi máy.</p>
<ul>
  <li><b>Start</b>: chạy bot cho máy này. <b>Start All / Stop All</b>: chạy / dừng mọi máy.</li>
  <li><b>Hồ sơ (profile)</b>: lưu nhiều bộ cấu hình, bấm tên để chuyển nhanh, <b>+</b> để thêm, biểu tượng thùng rác để xoá.</li>
  <li><b>Server</b> và <b>nền văn minh</b>: bot tự nhận; có thể đặt tay nếu nhận sai.</li>
  <li><b>Maximize</b>: phóng to / thu nhỏ cửa sổ giả lập của máy này.</li>
  <li><b>Active</b>: kích hoạt máy này để Start All tính tới.</li>
</ul>
"""),
    ("Join Monster War", """
<h2>Join Monster War</h2>
<p>Bot tham gia đánh quái (boss) của liên minh.</p>
<ul>
  <li>Tích các loại boss muốn đánh.</li>
  <li>Chọn lượng stamina được phép dùng (<b>ALL</b>, 100 … 500 hoặc <b>No</b>).</li>
  <li>Chọn đội quân dùng để đi đánh (Troop 1–8).</li>
  <li>Cấp độ Viking khi tự gọi (Summon): Easy / Normal / Hard / Hell.</li>
</ul>
"""),
    ("Daily Activities", """
<h2>Daily Activities</h2>
<p>Tích các nhiệm vụ hằng ngày muốn bot làm. Mỗi nhiệm vụ làm <b>một lần mỗi ngày</b>, sang giờ reset server
(đặt ở màn Home) thì làm lại.</p>

<h3>Các nút</h3>
<ul>
  <li><b>Apply ALL</b>: chép cấu hình tab này sang mọi máy khác.</li>
  <li><b>Reset progress</b>: cho tất cả nhiệm vụ về "chưa làm" để bot làm lại ngay. Dùng khi game lỗi mà bot đã ghi là xong.</li>
</ul>

<h3>General</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Mục</th><th>Chọn gì &rarr; kết quả</th></tr>
<tr><td><b>Buy Stamina</b></td><td>0 / 10 / 16 / 20. Mua số thể lực đã chọn; 0 = không mua.</td></tr>
<tr><td><b>Buy Hammer</b></td><td>Tích: mua hết búa đang bán.</td></tr>
<tr><td><b>Crazy Eggs</b></td><td>0 / 1h / 2h / 3h / 4h. Đập trứng Crazy Eggs, chưa vỡ đủ 4 quả thì thử lại sau chừng ấy giờ. 0 = không làm.</td></tr>
<tr><td><b>Claim Event Gifts</b></td><td>Tích (mặc định): nhận quà ở Valuable Event, Super Value Return, Back to Territory, Event Center.</td></tr>
</table>

<h3>Selection Daily</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Nhiệm vụ</th><th>Kết quả</th></tr>
<tr><td><b>Offering</b></td><td>Chọn số lần Offer Gems (0 = không làm). <b>Mỗi lần tốn kim cương.</b></td></tr>
<tr><td><b>City Tax</b></td><td>Thu thuế theo nhóm <i>City Tax</i> bên dưới.</td></tr>
<tr><td><b>Gold Levy</b></td><td>Nhận vàng từ lượt Levy miễn phí (không tốn kim cương).</td></tr>
<tr><td><b>Troop Training</b></td><td>Hoàn thành nhiệm vụ huấn luyện lính.</td></tr>
<tr><td><b>Troop Healing</b></td><td>Hoàn thành nhiệm vụ chữa lính (mặc định tích).</td></tr>
<tr><td><b>Trap Building</b></td><td>Hoàn thành nhiệm vụ xây bẫy.</td></tr>
<tr><td><b>Alliance Donation</b></td><td>0 / 1h–4h (mặc định 4h). Donate hết lượt miễn phí ở Alliance Science, lặp lại sau chừng ấy giờ. Không tốn kim cương.</td></tr>
<tr><td><b>Alliance Help</b></td><td>0 / 1h–4h. Giúp đỡ cả liên minh (Help All), lặp lại sau chừng ấy giờ.</td></tr>
<tr><td><b>Black Market</b></td><td>Hoàn thành nhiệm vụ mua ở Black Market (món trả bằng kim cương bị bỏ qua).</td></tr>
<tr><td><b>General Enhancing</b></td><td>Cultivate tướng 5 lần bằng vàng.</td></tr>
<tr><td><b>Wheel of Fortune</b></td><td>Quay vòng quay: 100 Spins nếu đủ chip, không thì một lần 10 Spins.</td></tr>
<tr><td><b>Patrol</b></td><td>Hoàn thành nhiệm vụ Patrol.</td></tr>
<tr><td><b>Material Composing</b></td><td>Ghép nguyên liệu để đủ nhiệm vụ.</td></tr>
<tr><td><b>Research</b></td><td>Nghiên cứu công nghệ.</td></tr>
<tr><td><b>Trade Carriage</b></td><td>Hoàn thành nhiệm vụ Trade Carriage.</td></tr>
<tr><td><b>Greet Champion</b></td><td>Chào Champion đủ lượt.</td></tr>
<tr><td><b>Ranger Knight</b></td><td>Hoàn thành nhiệm vụ Ranger Knight Order (mặc định tích).</td></tr>
</table>
<p>Khi mọi nhiệm vụ đã tích xong, phần thưởng rương Activity được nhận.</p>

<h3>City Tax</h3>
<p>Mỗi loại tài nguyên (Food, Wood, Stone, Iron) chọn <b>số lần thu</b>. Ô <b>Free</b> chỉ tích được ở một loại:
loại đó thu hết lượt miễn phí rồi thêm số lần đã chọn.</p>

<h3>Alliance Shop</h3>
<p>Tích các vật phẩm muốn mua ở cửa hàng liên minh (mặc định tích sẵn). Mỗi món mua tối đa số lượt trong ngày.
Tích thêm món mới thì phần đó được mua tiếp.</p>

<h3>Lưu ý</h3>
<ul>
  <li><b>Thời gian:</b> "một ngày" tính theo <b>giờ reset server</b> đặt ở màn Home. Hãy đặt đúng giờ này,
      nếu sai bot sẽ tưởng nhiệm vụ đã làm xong hoặc chưa tới ngày mới.</li>
  <li><b>Giờ máy tính:</b> bot so giờ reset với đồng hồ của máy tính, nên <b>giờ và múi giờ của Windows phải đúng</b>.
      Đồng hồ lệch thì ngày mới bắt đầu sai lúc. Chưa đặt giờ reset thì bot tạm tính ngày mới từ 0h theo giờ máy tính.</li>
  <li>Offering là việc duy nhất tốn kim cương và mặc định là 0; bạn tự chọn số lần.</li>
  <li>Muốn biết hôm nay đã làm xong gì: tab <b>Logs &rarr; History</b>.</li>
</ul>
"""),
    ("Event", """
<h2>Event</h2>
<p>Tích event và chọn mục tiêu cho từng nhiệm vụ; bot làm đủ mục tiêu rồi nhận thưởng event.
Nhiệm vụ mở theo ngày (Day 1 &rarr; Day 7), ngày chưa mở sẽ được làm khi tới ngày.</p>

<h3>Cách dùng</h3>
<ul>
  <li><b>Ô tích ở tiêu đề nhóm</b>: bật / tắt cả event đó.</li>
  <li><b>Ô chọn số</b>: mục tiêu của nhiệm vụ. Chọn <b>0</b> = không làm nhiệm vụ đó.
      Mặc định là mức cao nhất (làm hết); hạ xuống nếu muốn tiết kiệm.</li>
  <li>Rê chuột vào một nhiệm vụ để biết nó mở vào <b>Day</b> nào.</li>
  <li>Tiêu đề nhóm hiện <b>thời gian còn lại</b> của event.</li>
  <li><b>Apply ALL</b>: chép cấu hình sang mọi máy. <b>Reset progress</b>: cho nhiệm vụ về "chưa làm" để bot làm lại.</li>
</ul>

<h3>Gather Troops</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Nhiệm vụ</th><th>Kết quả</th></tr>
<tr><td><b>Cultivate Generals</b> (Day 1)</td><td>Hoàn thành nhiệm vụ Cultivate tướng.</td></tr>
<tr><td><b>Ground / Mounted / Ranged Troop, Siege Machine</b> (Day 2–4)</td><td>Chọn số lính cần train. Ô dạng <code>20000 (Lv 13)</code> = số lượng kèm cấp lính (Lv 7–13). Mặc định 20000.</td></tr>
<tr><td><b>Trap Factory</b> (Day 4)</td><td>Chọn số bẫy cần xây, 1000 – 7000 (Lv 3–6). Mặc định 7000.</td></tr>
</table>

<h3>King's Path</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Nhiệm vụ</th><th>Mục tiêu có thể chọn</th></tr>
<tr><td><b>City Tax</b> (Day 5)</td><td>Số lần thu thuế: 3 … 110</td></tr>
<tr><td><b>Patrol</b> (Day 2)</td><td>Tiến độ Patrol: 50 … 200</td></tr>
<tr><td><b>Donate</b> (Day 5)</td><td>Số lần donate liên minh: 10 … 60</td></tr>
<tr><td><b>Train Troop</b> (Day 3)</td><td>Số lính train: 2.000 … 200.000</td></tr>
<tr><td><b>Heal</b> (Day 3)</td><td>Số lính chữa: 1.000 … 50.000</td></tr>
<tr><td><b>Wheel</b> (Day 4)</td><td>Số lần quay: 5 … 100</td></tr>
<tr><td><b>Refine Equipment</b> (Day 4)</td><td>Số lần luyện trang bị: 10 … 100</td></tr>
<tr><td><b>Black Market</b> (Day 5)</td><td>Số lần mua: 1 … 100</td></tr>
</table>

<h3>3-Day Event</h3>
<ul>
  <li><b>Alliance</b> (0 / 10 / 30 / 60) và <b>Heal</b> (0 … 30.000): mục tiêu của hai nhiệm vụ.</li>
  <li><b>Redeem priority</b>: danh sách quà đổi, xếp thứ tự bằng nút <b>Up / Down</b>. Quà ở trên được ưu tiên đổi trước;
      quà nào chưa đủ điểm thì bỏ qua.</li>
</ul>

<h3>Lưu ý</h3>
<ul>
  <li><b>Thời gian:</b> ngày của event (Day 1, 2, ...) đổi theo <b>giờ reset server</b> đặt ở màn Home; hãy đặt đúng giờ này.
      Nhiệm vụ của ngày chưa tới sẽ được làm khi tới ngày, và hết giờ event thì không làm được nữa nên nên để bot chạy trước khi event kết thúc.</li>
  <li><b>Giờ máy tính:</b> giờ và múi giờ của Windows phải đúng, vì bot dùng đồng hồ máy tính để biết event còn bao lâu và khi nào làm lại.</li>
  <li>Event 3 ngày chỉ bắt đầu sau khi event 7 ngày (King's Path) kết thúc.</li>
  <li>Event chưa mở hoặc đã hết thì bot bỏ qua, không báo lỗi.</li>
</ul>
"""),
    ("Open Gift Box", """
<h2>Open Gift Box</h2>
<p>Mở các loại hộp quà trong kho đồ.</p>
<ul>
  <li>Tích <b>All</b> để mở mọi loại, hoặc tích riêng từng loại.</li>
</ul>
"""),
    ("Alliance Capacity", """
<h2>Alliance Capacity</h2>
<p>Góp tài nguyên / gem cho sức chứa của liên minh.</p>
<ul>
  <li>Mục <b>Times</b>: số lần góp.</li>
</ul>
"""),
    ("Black Market", """
<h2>Black Market</h2>
<p>Tự mua hàng ở Black Market.</p>
<ul>
  <li><b>Setting</b>: <i>CheckGold</i> (vàng xuống dưới 2.000.000 thì dừng), <i>Refresh</i> (số lần làm mới), <i>Quantity Buy</i> (số lần mua).</li>
  <li><b>General</b>: tài nguyên, Chips, Stamina, Tribute...</li>
  <li>Các nhóm còn lại: tích từng món muốn mua.</li>
</ul>
"""),
    ("Recruit General", """
<h2>Recruit General</h2>
<p>Tuyển tướng trong game.</p>
<ul>
  <li><b>Setting</b>: <i>Open Gold</i>, số lần Refresh, và cách mua: <i>Recruit General</i> hoặc <i>Buy General Token</i> (chỉ chọn một).</li>
  <li><b>Generals</b>: tìm tướng theo tên, lọc theo civ / loại, tích tướng cần tuyển và chọn số lượng.
      Tướng đã tích vẫn được giữ khi đổi bộ lọc.</li>
</ul>
"""),
    ("Find Boss", """
<h2>Find Boss</h2>
<p>Bot quét bản đồ thế giới để tìm boss quanh thành.</p>
<ul>
  <li><b>Góc quét</b>: góc bắt đầu và kết thúc (0–360°, bước 15°, tính theo màn hình).</li>
  <li><b>Auto</b>: chia đều 360° cho mọi tài khoản cùng server để các máy không quét trùng nhau.</li>
  <li><b>Bán kính</b>: quét xa tới đâu từ thành.</li>
  <li><b>Chia sẻ liên minh</b>: gửi toạ độ boss tìm được cho liên minh.</li>
  <li>Tích các loại boss cần tìm.</li>
</ul>
"""),
    ("Craft", """
<h2>Craft</h2>
<p>Chế tạo trang bị.</p>
<ul>
  <li><b>Overview</b>: <i>Claim event gifts</i> và thứ tự ưu tiên các hộp quà đổi (nút lên / xuống để đổi thứ tự).</li>
  <li><b>Equipment</b>: tìm theo tên, lọc theo loại, tích trang bị cần chế và nhập số lượng (mặc định 1).</li>
</ul>
<p>Chế xong một món, số lượng của món đó tự giảm; về 0 thì bỏ khỏi danh sách.</p>
"""),
    ("Gather Resources", """
<h2>Gather Resources</h2>
<p>Gửi đội đi thu thập tài nguyên.</p>
<ul>
  <li>Bấm <b>+ Add troop</b> để thêm một đội (có giới hạn tối đa).</li>
  <li>Mỗi đội chọn loại tài nguyên (Food, Wood, Stone, Iron, Gems) và cấp mỏ.</li>
  <li>Bot không chọn preset quân: tới màn March là bấm March luôn.</li>
</ul>
"""),
    ("Refine Equipment", """
<h2>Refine Equipment</h2>
<p>Tinh luyện 6 trang bị của một tướng: bot mở danh sách tướng (••• → Generals), chọn tướng đầu tiên rồi tinh luyện từng trang bị.</p>
<ul>
  <li><b>General</b>: <i>Favorite generals</i> (lọc tướng yêu thích) và loại tướng; bot luôn chọn tướng đầu tiên sau khi lọc.</li>
  <li>Mỗi trang bị (Weapon, Armor, Boots, Helmet, Pants, Ring) có danh sách thuộc tính riêng: bấm <b>+ Add line</b> để thêm dòng cần có (tối đa 4, vì trang bị có 4 dòng tinh luyện); mỗi dòng chọn một thuộc tính, màu tối thiểu (Orange / Gold) và ô <b>Lock</b> (khoá dòng lại khi đã ra đúng); nút thùng rác xoá dòng. ô <b>Max refines (per equipment)</b> là số lần Refine tối đa cho riêng trang bị đó (100 đến 1000 hoặc ALL = không giới hạn).</li>
  <li>Trang bị không tích dòng nào thì bỏ qua.</li>
</ul>
<p><i>Đang phát triển:</i> bot đã mở được màn Refine Equipment của từng trang bị nhưng chưa đọc được 4 dòng kết quả nên chưa tự bấm Refine.</p>
"""),
    ("Logs", """
<h2>Logs</h2>
<p>Nhật ký của máy đang mở.</p>
<ul>
  <li><b>Info</b>: thông báo tức thời của bot, không lưu lại.</li>
  <li><b>History</b>: các sự kiện quan trọng (đã làm xong gì, lỗi gì), được lưu để xem lại sau.</li>
</ul>
<p>Bot không chạy như ý thì đây là nơi đầu tiên cần xem.</p>
"""),
    ("Xử lý sự cố", """
<h2>Xử lý sự cố</h2>
<ul>
  <li><b>Load Devices không thấy giả lập</b>: kiểm tra giả lập đã bật, bật ADB trong cài đặt giả lập,
      và khoảng Start / End port ở Home có chứa cổng của máy.</li>
  <li><b>Bot đứng yên ở một màn</b>: xem tab Logs; đảm bảo giả lập đặt đúng độ phân giải, game để ngôn ngữ tiếng Anh.</li>
  <li><b>Bot không làm một việc</b>: việc đó có thể đã làm xong trong ngày (chờ giờ reset) hoặc chưa được tích.</li>
  <li><b>Mã kích hoạt hết hạn</b>: bot dừng và app đóng; nhập mã mới khi mở lại.</li>
</ul>
"""),
]
