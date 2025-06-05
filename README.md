# NKU-SoftwareEngineering
22级 南开大学软件工程课程大作业 智慧海洋牧场可视化系统

## 🏗️ 项目结构
```
    NKU-SoftwareEngineering/
    ├── README.md
    ├── Visualisation_System
    │   ├── .gitignore
    │   ├── __pycache__
    │   │   └── fish_price_spider.cpython-310.pyc
    │   ├── app.py
    │   ├── fish_price_spider.py
    │   ├── static
    │   │   ├── images
    │   │   │   ├── image1.jpg
    │   │   │   ...
    │   │   │   ├── logo.png
    │   │   │   ├── title_image.png
    │   │   │   └── title_image_withoutwords.png
    │   │   ├── pictures_fish
    │   │   │   ├── 12277661_195617074000_2.jpg
    │   │   │   └── 1954049_164606361419_2.jpg
    │   │   ├── style.css
    │   │   ├── upload data
    │   │   │   ├── 测试.xls
    │   │   │   └── 测试2.xlsx
    │   │   ├── videos
    │   │   │   └── test.mp4
    │   │   └── visualsystem.sql
    │   └── templates
    │       ├── AI_center.html
    │       ├── add_user.html
    │       ├── admin_logs.html
    │       ├── admin_users.html
    │       ├── ai_qa.html
    │       ├── base.html
    │       ├── datas.html
    │       ├── edit_user.html
    │       ├── fish_farm_detail.html
    │       ├── fish_farms.html
    │       ├── fish_price_today.html
    │       ├── home.html
    │       ├── login.html
    │       ├── register.html
    │       ├── upload_fishes.html
    │       ├── wat.html
    │       └── wat.js
    ├── data_clean
    │   ├── water_data_clean.py
    │   └── water_data_leadin.py
    ├── structure.txt
    └── 水质数据（已清理）
        ├── fish_farm_summary.csv
        └── water_data_clean
            ├── 2020-05
            │....
```
### 📁 主要目录说明

-   **`data_clean/`** - 清理数据脚本
-   **`test/`** - 项目test脚本
-   **`Visualisation_System/`** - 可视化文件
-   **`水质数据（已清理）/`** - 清理后水质数据
## 🔧安装依赖

```bash
# 1. 创建并激活conda环境 (如果尚未创建)
conda create -n softw python=3.12
conda activate softw

# 2. 安装依赖
pip install flask matplotlib requests pymysql werkzeug pandas numpy zhipuai mysql-connector-python

```

## 🚀运行示例
```bash
python app.py
```