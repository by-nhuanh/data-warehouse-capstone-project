# TÀI LIỆU HƯỚNG DẪN TRUY CẬP & QUẢN TRỊ MÔI TRƯỜNG DATA LAKEHOUSE DÙNG CHUNG

---

## 1. Tổng quan Môi trường

### 1.1. Mục đích
Tài liệu này quy định cấu trúc hạ tầng, quy trình vận hành và quy tắc quản trị môi trường Cloud-Native Data Lakehouse cho dự án Phân tích và Dự báo Rủi ro Tín dụng Bán lẻ (sử dụng bộ dữ liệu Home Credit gồm 7 phân hệ)[cite: 12]. Môi trường này phục vụ đồng thời cho 3 mục tiêu: Data Engineering (dbt), BI Analytics (Power BI / Metabase) và In-Database Machine Learning (Feature Mart)[cite: 12].

### 1.2. Kiến trúc Hạ tầng & Luồng Dữ liệu
Hệ thống kết hợp mô hình lưu trữ persistent trên Google Drive và động cơ tính toán nhúng DuckDB In-Process Engine trên Google Colab[cite: 12].

```mermaid
flowchart TD
    SRC["📂 HOME CREDIT DATASET<br/>(7 CSV Files)"]

    subgraph GDRIVE["📁 GOOGLE DRIVE DÙNG CHUNG (Data_Lakehouse_Project)"]
        direction TB
        
        subgraph PARQUET_STORAGE["📦 data/ (Parquet Persistent Storage)"]
            BRONZE["🔴 bronze/<br/>Raw Data Zone"]
            SILVER["🟡 silver/<br/>Cleaned & Standardized"]
            GOLD["🟢 gold/<br/>Kimball Star Schema & Feature Mart"]
        end
        
        subgraph DB_STORAGE["🗄️ database/"]
            DUCK_DB[("credit_lakehouse.duckdb")]
        end
    end

    subgraph COLAB["⚡ GOOGLE COLAB (Compute Engine)"]
        ENGINE["🦆 DuckDB Engine (OLAP)"]
        
        subgraph WORKLOADS["Giai đoạn Xử lý & Phân tích"]
            DBT["🔄 dbt Transformations<br/>(Bronze ➔ Silver ➔ Gold)"]
            DQ["✅ Data Quality Testing"]
            ML_MART["⚙️ In-Database ML<br/>Feature Mart"]
        end
        
        ENGINE --> DBT
        ENGINE --> DQ
        ENGINE --> ML_MART
    end

    subgraph CONSUMPTION["🎯 TẦNG TIÊU THỤ & TRỰC QUAN HÓA"]
        EXPORTS["📄 Gold Parquet Exports"]
        WIDE_FEAT["📋 Wide Table Features"]
        
        PBI["📊 Power BI Desktop"]
        UI["🌐 Metabase / Streamlit UI"]
        ML_MODELS["🤖 Python ML Models<br/>(XGBoost / Sklearn)"]
        
        EXPORTS --> PBI
        EXPORTS --> UI
        WIDE_FEAT --> ML_MODELS
    end

    SRC --> GDRIVE
    GDRIVE == "Mount Drive" ==> COLAB
    
    DBT --> EXPORTS
    ML_MART --> WIDE_FEAT

    classDef default font-family:arial,font-size:13px;
    classDef srcStyle fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
    classDef gdriveStyle fill:#f1f8e9,stroke:#558b2f,stroke-width:2px,color:#2e7d32;
    classDef colabStyle fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#e65100;
    classDef consumeStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;
    classDef dbStyle fill:#fffde7,stroke:#fbc02d,stroke-width:2px,color:#f57f17;

    class SRC srcStyle;
    class GDRIVE gdriveStyle;
    class COLAB colabStyle;
    class CONSUMPTION consumeStyle;
    class DUCK_DB dbStyle;
```[cite: 13]

### 1.3. Công nghệ Cốt lõi (Tech Stack)
* **Storage Layer:** Apache Parquet (Columnar storage) lưu trữ persistent trên Google Drive[cite: 13].
* **Compute Engine:** DuckDB (In-Process OLAP Engine) xử lý truy vấn dữ liệu lớn zero-copy[cite: 13].
* **Transformation & Lineage:** `dbt-duckdb` quản lý pipeline Medallion và Data Lineage (DAG)[cite: 13].
* **Analytics & ML:** Power BI Desktop / Metabase cho BI; Scikit-Learn & XGBoost cho ML Model[cite: 13].

---

## 2. Cấu trúc Thư mục Chuẩn trên Google Drive

Tất cả thành viên trong nhóm phải tuân thủ đúng cấu trúc thư mục sau tại `/content/drive/MyDrive/Data_Lakehouse_Project/`[cite: 14]:

```mermaid
graph TD
    ROOT["📁 Data_Lakehouse_Project/"]
    
    NOTEBOOKS["📁 notebooks/"]
    NOTEBOOK_FILE["📄 Setup_Environment_Lakehouse.ipynb"]
    
    DATA["📁 data/"]
    RAW["📁 raw/ (7 CSV Files)"]
    BRONZE["📁 bronze/ (Raw Parquet)"]
    SILVER["📁 silver/ (Cleaned Data)"]
    GOLD["📁 gold/ (Kimball & Feature Mart)"]
    
    DATABASE["📁 database/"]
    DB_FILE[("📄 credit_lakehouse.duckdb")]
    
    EXPORTS["📁 exports/"]
    PBI_EXP["📁 powerbi/"]
    ML_EXP["📁 ml/"]
    
    LOGS["📁 logs/"]
    
    DOCS["📁 docs/"]
    DOC_FILE["📄 README_Environment.md"]

    ROOT --> NOTEBOOKS
    ROOT --> DATA
    ROOT --> DATABASE
    ROOT --> EXPORTS
    ROOT --> LOGS
    ROOT --> DOCS

    NOTEBOOKS --> NOTEBOOK_FILE
    DATA --> RAW
    DATA --> BRONZE
    DATA --> SILVER
    DATA --> GOLD
    DATABASE --> DB_FILE
    EXPORTS --> PBI_EXP
    EXPORTS --> ML_EXP
    DOCS --> DOC_FILE

    classDef folderStyle fill:#e3f2fd,stroke:#1565c0,stroke-width:1.5px,color:#0d47a1;
    classDef fileStyle fill:#fffde7,stroke:#fbc02d,stroke-width:1.5px,color:#f57f17;
    classDef dbStyle fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;

    class ROOT,NOTEBOOKS,DATA,RAW,BRONZE,SILVER,GOLD,DATABASE,EXPORTS,PBI_EXP,ML_EXP,LOGS,DOCS folderStyle;
    class NOTEBOOK_FILE,DOC_FILE fileStyle;
    class DB_FILE dbStyle;
```[cite: 14]

---

## 3. Hướng dẫn Truy cập Môi trường trên Colab

### 3.1. Quyền truy cập Google Drive
Mỗi thành viên mở Google Drive cá nhân $\rightarrow$ Mục *"Được chia sẻ với tôi" (Shared with me)* $\rightarrow$ Chuột phải vào `Data_Lakehouse_Project` $\rightarrow$ Chọn **"Thêm lối tắt vào Drive" (Add shortcut to Drive)**[cite: 14].

### 3.2. Quy trình thực thi Notebook `Setup_Environment_Lakehouse.ipynb`
Mỗi khi bắt đầu ca làm việc trên Google Colab, thành viên mở file notebook khởi tạo và thực thi lần lượt 2 Cell chính[cite: 14]:

* **Cell 1 — Mount Google Drive & Kiểm tra Thư mục:**[cite: 14]
  * Thực hiện Mount Google Drive cá nhân vào môi trường runtime của Colab[cite: 14].
  * Thiết lập đường dẫn làm việc gốc (`PROJECT_PATH`)[cite: 14].
  * Tự động kiểm tra tính tồn tại của cấu trúc thư mục và xác nhận quyền đọc/ghi (Read/Write)[cite: 14].
* **Cell 2 — Khởi tạo DuckDB Engine & Tự động Tạo Schemas:**[cite: 14]
  * Cài đặt tự động gói thư viện `duckdb` (nếu chưa có)[cite: 14].
  * Kết nối tới file cơ sở dữ liệu persistent `/database/credit_lakehouse.duckdb`[cite: 14].
  * Tự động kích hoạt extension `httpfs` và cấu hình giới hạn RAM/Threads phù hợp với tài nguyên Colab[cite: 14].
  * Tự động khởi tạo 3 Schemas Medallion: `bronze`, `silver`, `gold` (nếu chưa tồn tại)[cite: 14].
  * Xuất ra console màn hình log xác nhận trạng thái môi trường sẵn sàng[cite: 14].

### 3.3. Kiểm tra Môi trường sau khi Kết nối
Sau khi thực thi xong Cell 2, kiểm tra màn hình output bắt buộc phải hiển thị đủ các dòng trạng thái sau[cite: 14, 15]:

```text
✓ Google Drive connected successfully
✓ Project directory structure validated
✓ DuckDB connected: /content/drive/MyDrive/Data_Lakehouse_Project/database/credit_lakehouse.duckdb
✓ Schema 'bronze' ready
✓ Schema 'silver' ready
✓ Schema 'gold' ready
✓ Parquet storage directories online
==================================================
✅ HỆ THỐNG LAKEHOUSE ĐÃ SẴN SÀNG 100%
==================================================
Danh sách Schemas hiện có trong Lakehouse: ['bronze', 'gold', 'main', 'silver', 'information_schema', 'main', 'pg_catalog', 'main']
```[cite: 15]

---

## 4. Kiến trúc Medallion & Quy ước Đặt tên (Naming Conventions)

### 4.1. Định nghĩa 3 Tầng Dữ liệu
* **Tầng `bronze` (Raw Zone):** Lưu giữ nguyên bản dữ liệu thô từ 7 bảng gốc Home Credit. Không thay đổi tên cột hay kiểu dữ liệu[cite: 15].
* **Tầng `silver` (Cleaned Zone):** Lưu trữ dữ liệu đã làm sạch, xử lý missing values, loại bỏ outlier (`DAYS_EMPLOYED`), khử trùng lặp và chuyển đổi kiểu dữ liệu chuẩn[cite: 15].
* **Tầng `gold` (Business & Feature Mart Zone):** Tổ chức theo mô hình đa chiều Star Schema chuẩn Ralph Kimball (Bảng Chiều Dim, Bảng Sự kiện Fact) và bảng phẳng Feature Mart phục vụ In-Database ML[cite: 15].

### 4.2. Quy ước Đặt tên (Naming Rules)
Tất cả thành viên bắt buộc tuân thủ quy tắc đặt tên bảng và đối tượng dữ liệu trong DuckDB[cite: 15]:

| Đối tượng | Quy tắc đặt tên | Ví dụ |
| :--- | :--- | :--- |
| **Schemas** | Viết thường, cố định | `bronze`, `silver`, `gold`[cite: 16] |
| **Tên Bảng / Tệp** | `snake_case` | `application_clean`, `bureau_processed`[cite: 16] |
| **Dimension Tables (Tầng Gold)** | `dim_<tên_chiều>` | `gold.dim_customer`, `gold.dim_loan_product`[cite: 16] |
| **Fact Tables (Tầng Gold)** | `fact_<tên_sự_kiện>` | `gold.fact_monthly_loan_balance`, `gold.fact_loan_payment`[cite: 16] |
| **Feature Mart (Tầng Gold)** | `wide_table_<mục_đích>` | `gold.wide_table_credit_features`[cite: 16] |

---

## 5. Quy trình Vận hành Dữ liệu (Data Pipeline Flow)

Luồng chuyển đổi dữ liệu trong hệ thống được thực hiện theo chu trình khép kín[cite: 16]:

```text
[Dataset CSVs] ──(Ingestion)──► [bronze] ──(dbt Clean)──► [silver] ──(Kimball/dbt)──► [gold] ──► [Power BI & ML]
```[cite: 16]

1. **Ingestion (Nạp dữ liệu):** Đọc các file CSV thô từ `/data/raw/` và ghi vào DuckDB schema `bronze` dưới dạng bảng hoặc file Parquet[cite: 16].
2. **Cleaning & Standardizing (Làm sạch):** Áp dụng `dbt-duckdb` để làm sạch và ghi kết quả vào schema `silver`[cite: 16].
3. **Dimensional Modeling (Mô hình hóa):** Biên dịch dữ liệu Silver thành các bảng `dim_*` và `fact_*` tại schema `gold`[cite: 16].
4. **Export & Consumption (Xuất & Tiêu thụ):** Xuất bảng tầng Gold ra file Parquet để phục vụ vẽ Power BI Dashboards và làm tập đặc trưng cho Machine Learning[cite: 16].

---

## 6. Quy tắc Quản trị Môi trường & Tránh Xung đột Truy cập

### 6.1. Nguyên lý Đồng thời của DuckDB trên Google Drive (QUAN TRỌNG)
> **LƯU Ý KỸ THUẬT:** DuckDB là cơ sở dữ liệu dạng tệp (File-based OLAP Database)[cite: 17]. Mặc dù file `.duckdb` được lưu trữ trên Google Drive dùng chung, Google Drive **KHÔNG PHẢI** là một Database Server đa người dùng (Multi-user Server)[cite: 17]. **Tại một thời điểm, chỉ duy nhất MỘT phiên (session) Colab được phép ghi (WRITE) vào file `credit_lakehouse.duckdb`.**[cite: 17]

### 6.2. Phân quyền (Read/Write Rules)
Để tránh xung đột khóa file (File Locking Error) hoặc ghi đè làm hỏng dữ liệu, nhóm quy định[cite: 17]:

| Phạm vi công việc | Quy định thao tác |
| :--- | :--- |
| **Nạp dữ liệu, chạy dbt pipeline Bronze $\rightarrow$ Silver $\rightarrow$ Gold.** | Chỉ 01 người chạy pipeline ghi DB tại một thời điểm. Sau khi hoàn tất phải ngắt kết nối (`con.close()`)[cite: 17]. |
| **Đọc dữ liệu tầng gold để vẽ biểu đồ.** | Chỉ đọc các file Parquet đã xuất ra thư mục `/exports/powerbi/` hoặc kết nối DuckDB ở chế độ `read_only=True`[cite: 17]. |
| **Trích xuất Feature Mart tầng gold để huấn luyện mô hình.** | Đọc bảng `gold.wide_table_credit_features` dạng `read_only=True` hoặc load trực tiếp file Parquet[cite: 17]. |

### 6.3. Quy trình Quản trị Thay đổi & Sao lưu (Backup)
* **Không tự ý đổi cấu trúc:** Không tự ý `DROP`, `ALTER` hoặc đổi tên các Schema/Bảng dùng chung khi chưa thống nhất với nhóm[cite: 17].
* **Quy trình Ngắt kết nối:** Luôn gọi lệnh `con.close()` ở cuối mỗi buổi làm việc để giải phóng lock file trên Drive[cite: 17].
* **Sao lưu định kỳ (Backup):** Cuối mỗi ngày làm việc, thành viên phụ trách ca có nhiệm vụ sao lưu file `credit_lakehouse.duckdb` thành phiên bản dạng `credit_lakehouse_YYYYMMDD.duckdb` lưu trong thư mục `/database/backup/`[cite: 17].

---

## 7. Truy cập Dữ liệu cho BI Analytics (Power BI / Metabase)

Thành viên phụ trách Trực quan hóa dữ liệu (Dashboard) thực hiện truy xuất dữ liệu theo các kênh[cite: 18]:

1. **Nguồn Dữ liệu:** Sử dụng trực tiếp các file Parquet đã được xuất chuẩn hóa từ tầng `gold` tại thư mục `/exports/powerbi/` (gồm các file `dim_customer.parquet`, `fact_monthly_loan_balance.parquet`,...)[cite: 18].
2. **Thao tác trên Power BI Desktop:**[cite: 18]
   * Mở Power BI Desktop $\rightarrow$ Select **Get Data** $\rightarrow$ **Folder** hoặc **Parquet**[cite: 18].
   * Trỏ đường dẫn đến thư mục Google Drive đã đồng bộ trên máy tính cá nhân (`Google Drive/Data_Lakehouse_Project/exports/powerbi/`)[cite: 18].
   * Tiến hành Link các bảng theo mô hình Star Schema chuẩn Kimball đã thiết kế[cite: 18].

---

## 8. Truy cập Feature Mart cho Machine Learning

Thành viên phụ trách huấn luyện mô hình Dự báo Rủi ro Tín dụng ($PD = P(TARGET=1)$) truy cập dữ liệu ML theo đúng nguyên tắc Point-in-Time Correctness[cite: 18]:

1. **Vị trí Tập đặc trưng:** Bảng phẳng `gold.wide_table_credit_features` (hoặc file `/exports/ml/wide_table_credit_features.parquet`)[cite: 18].
2. **Đặc trưng tích hợp:** Chứa 100+ thuộc tính đặc trưng được tổng hợp từ dữ liệu nhân khẩu học, lịch sử tín dụng bên ngoài (CIC), dư nợ hàng tháng và hành vi trả nợ quá hạn (DPD)[cite: 18].
3. **Quy trình huấn luyện:** Trích xuất bảng Feature Mart trực tiếp sang dạng Pandas DataFrame / Apache Arrow trong Python Colab để chạy các mô hình Logistic Regression, XGBoost, LightGBM[cite: 18].

---

## 9. Truy cập Giao diện Trực quan (UI/Dashboard Demo)

* **Trạng thái Triển khai UI:** Giao diện Web UI (Metabase / Streamlit Dashboard) hiện được triển khai ở **giai đoạn Demo thử nghiệm**[cite: 18]. Đường link truy cập công khai sẽ được hệ thống tạo động và cập nhật trực tiếp tại nhóm làm việc mỗi khi máy chủ Demo trên Colab được kích hoạt[cite: 18].
* **Phương thức kích hoạt Demo Web UI (Streamlit trên Colab):**[cite: 18]
  Khi cần chạy Demo Web UI tương tác cho nhóm hoặc báo cáo[cite: 18]:
  1. Mở notebook `Demo_Streamlit_UI.ipynb` trên Colab và bấm chạy[cite: 18].
  2. Màn hình sẽ xuất ra **URL Public** (dạng `https://xxxx.loca.lt`) do Localtunnel/Ngrok cấp kèm IP Password[cite: 18].
  3. Thành viên truy cập URL, dán IP Password để vào màn hình Web UI quản trị và xem biểu đồ trực tiếp từ DuckDB Gold Layer[cite: 18].

---

## 10. Xử lý Lỗi Thường gặp (Troubleshooting)

| Lỗi gặp phải | Nguyên nhân | Cách xử lý |
| :--- | :--- | :--- |
| **`FileNotFoundError: Data_Lakehouse_Project`** | Chưa thêm Shortcut thư mục dự án vào Drive cá nhân[cite: 19]. | Trên Google Drive, vào *"Được chia sẻ với tôi"* $\rightarrow$ Chuột phải thư mục dự án $\rightarrow$ Chọn *"Thêm lối tắt vào Drive"*[cite: 19]. |
| **`IOException: Could not set lock on file`** | Có thành viên khác đang mở kết nối DuckDB ở chế độ Write[cite: 19]. | Báo thành viên đó chạy `con.close()` ngắt session, hoặc chuyển câu lệnh kết nối của mình sang `duckdb.connect(db_path, read_only=True)`[cite: 19]. |
| **`CatalogException: Schema with name bronze does not exist`** | Chưa chạy Cell 2 khởi tạo môi trường[cite: 19]. | Chạy lại Cell 2 trong notebook `Setup_Environment_Lakehouse.ipynb`[cite: 19]. |
| **`Power BI error: File not found or in use`** | Google Drive Desktop trên PC chưa đồng bộ xong file Parquet mới[cite: 20]. | Kiểm tra ứng dụng Google Drive trên máy tính, đảm bảo trạng thái đã "Synced", hoặc kiểm tra tệp Parquet đã được xuất từ Colab chưa[cite: 20]. |

---

## 11. Checklist Kiểm tra trước khi Làm việc (Daily Checklist)

Trước khi bắt đầu thao tác dữ liệu mỗi ngày, mỗi thành viên thực hiện nhanh 4 bước kiểm tra[cite: 20]:

- [ ] **Check 1:** Đã Mount Google Drive và xác nhận thư mục `Data_Lakehouse_Project` tồn tại[cite: 20].
- [ ] **Check 2:** Đã thực thi xong Cell 2 và màn hình hiển thị đầy đủ 3 Schemas `bronze`, `silver`, `gold`[cite: 20].
- [ ] **Check 3:** Đã xác định đúng vai trò làm việc hôm nay (Nếu chỉ đọc/vẽ biểu đồ/chạy ML $\rightarrow$ Mở kết nối `read_only=True`)[cite: 20].
- [ ] **Check 4:** Đảm bảo thêm lệnh `con.close()` ở cuối notebook đang làm việc trước khi kết thúc ca[cite: 20].