CREATE TABLE water_quality_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    province VARCHAR(50),               -- 省份
    river_basin VARCHAR(100),           -- 流域
    section_name VARCHAR(255),          -- 断面名称（去除 HTML 标签）
    monitor_time DATETIME,              -- 监测时间（带年月日）
    quality_level VARCHAR(10),          -- 水质类别
    water_temp FLOAT,                   -- 水温 (℃)
    ph FLOAT,                           -- pH
    dissolved_oxygen FLOAT,             -- 溶解氧 (mg/L)
    conductivity FLOAT,                 -- 电导率 (μS/cm)
    turbidity FLOAT,                    -- 浊度 (NTU)
    cod_mn FLOAT,                       -- 高锰酸盐指数 (mg/L)
    ammonia_nitrogen FLOAT,             -- 氨氮 (mg/L)
    total_phosphorus FLOAT,            -- 总磷 (mg/L)
    total_nitrogen FLOAT,              -- 总氮 (mg/L)
    chlorophyll_a FLOAT,               -- 叶绿素α (mg/L)
    algae_density FLOAT,               -- 藻密度 (cells/L)
    site_status VARCHAR(50),           -- 站点情况（如：正常）
    farm_id INT,                       -- 渔场 ID
    farmer_id INT,                     -- 养殖户 ID
    source_date DATE                   -- 来源日期（如 2020-09-01）
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
