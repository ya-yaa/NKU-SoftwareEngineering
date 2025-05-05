import os
import json
import random
import csv

def collect_fish_farms(root_dir):
    """遍历所有json文件，提取唯一渔场组合"""
    fish_farm_map = {}
    fish_farm_id = 1

    for foldername, subfolders, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.json'):
                filepath = os.path.join(foldername, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    thead = data.get('thead', [])
                    tbody = data.get('tbody', [])

                    try:
                        prov_idx = thead.index("省份")
                        basin_idx = thead.index("流域")
                        site_idx = thead.index("断面名称")
                    except ValueError:
                        continue  # 跳过thead不全的文件

                    for row in tbody:
                        if len(row) < max(prov_idx, basin_idx, site_idx) + 1:
                            continue
                        key = (row[prov_idx], row[basin_idx], row[site_idx])
                        if key not in fish_farm_map:
                            fish_farm_map[key] = {
                                "渔场ID": fish_farm_id,
                                "养殖户ID": random.randint(1, 10)
                            }
                            fish_farm_id += 1
    return fish_farm_map

def process_and_save(root_dir, output_dir, fish_farm_map):
    """处理所有json文件，加上渔场ID和养殖户ID，并保存新文件"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for foldername, subfolders, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.json'):
                filepath = os.path.join(foldername, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    thead = data.get('thead', [])
                    tbody = data.get('tbody', [])

                    try:
                        prov_idx = thead.index("省份")
                        basin_idx = thead.index("流域")
                        site_idx = thead.index("断面名称")
                    except ValueError:
                        continue

                    if "渔场ID" not in thead:
                        thead.append("渔场ID")
                    if "养殖户ID" not in thead:
                        thead.append("养殖户ID")

                    for row in tbody:
                        if len(row) < max(prov_idx, basin_idx, site_idx) + 1:
                            continue
                        key = (row[prov_idx], row[basin_idx], row[site_idx])
                        farm_info = fish_farm_map.get(key, {"渔场ID": -1, "养殖户ID": -1})
                        row.extend([farm_info["渔场ID"], farm_info["养殖户ID"]])

                # 确定输出路径（保持子文件夹结构）
                relative_path = os.path.relpath(filepath, root_dir)
                output_path = os.path.join(output_dir, relative_path)
                output_folder = os.path.dirname(output_path)
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

def save_summary_csv(fish_farm_map, output_csv_path):
    """保存渔场总结表为CSV"""
    with open(output_csv_path, mode='w', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["省份", "流域", "断面名称", "渔场ID", "养殖户ID"])
        for (province, basin, site), ids in fish_farm_map.items():
            writer.writerow([province, basin, site, ids["渔场ID"], ids["养殖户ID"]])

def main():
    input_dir = "water_data"   # <<< 修改为你的输入根目录路径
    output_dir = "water_data_clean" # <<< 修改为你的输出根目录路径
    summary_csv_path = "fish_farm_summary.csv" # <<< 输出的csv位置，可以改成绝对路径

    print("开始收集渔场信息...")
    fish_farm_map = collect_fish_farms(input_dir)
    print(f"共发现 {len(fish_farm_map)} 个渔场。")

    print("保存渔场总表...")
    save_summary_csv(fish_farm_map, summary_csv_path)
    print(f"已生成总结表：{summary_csv_path}")

    print("开始处理并保存新文件...")
    process_and_save(input_dir, output_dir, fish_farm_map)
    print("所有文件处理完成！")

if __name__ == "__main__":
    main()
