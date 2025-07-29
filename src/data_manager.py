# data_manager.py

import pandas as pd
import os


class DataManager:
    """
    负责数据处理和保存。
    支持增量写入CSV文件。
    """

    def __init__(self, filename: str):
        """
        初始化DataManager，并设置好带时间戳的文件名。
        :param filename: 要保存的文件名
        """
        self.filename = filename
        # 确保目录存在
        path = os.path.join("boss_data", filename)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        print(f"准备将数据写入文件: {os.path.abspath(path)}")
        self.csv_filename = path
        self.json_filename = path.replace(".csv", ".json")
        # 总表文件也放在boss_data目录下
        self.master_filename = os.path.join("boss_data", "all.csv")

    def append_to_csv(self, job_data: dict):
        """
        将单条职位数据追加到CSV文件。
        如果文件不存在，则创建并写入表头。
        """
        if not job_data:
            return

        # 将单条字典数据转换为DataFrame
        df = pd.DataFrame([job_data])

        # 检查文件是否存在，以决定是否需要写入表头
        file_exists = os.path.exists(self.csv_filename)

        try:
            # 使用 mode='a' 进行追加写入
            # header=not file_exists 确保只在文件第一次创建时写入表头
            df.to_csv(
                self.csv_filename,
                mode="a",
                index=False,
                header=not file_exists,
                encoding="utf-8-sig",
            )
            print(f"  -> 已将职位 '{job_data['职位名称']}' 追加到CSV。")
        except Exception as e:
            print(f"  -> 追加到CSV文件时出错: {e}")

    def convert_csv_to_json(self):
        """
        读取已生成的CSV文件，并将其转换为JSON文件。
        """
        try:
            # 检查CSV文件是否存在
            if not os.path.exists(self.csv_filename):
                print("CSV文件不存在，无法转换为JSON。")
                return

            # 读取完整的CSV文件
            df = pd.read_csv(self.csv_filename)

            # 将DataFrame转换为JSON格式的字符串
            # orient='records' 会生成 [{column: value}, ...] 的列表形式
            # force_ascii=False 确保中文字符能正确显示，而不是被编码
            # indent=4 让JSON文件格式优美，易于阅读
            json_str = df.to_json(orient="records", force_ascii=False, indent=4)

            # 将JSON字符串写入文件
            with open(self.json_filename, "w", encoding="utf-8") as f:
                f.write(json_str)

            print(f"\nCSV文件已成功转换为JSON: {os.path.abspath(self.json_filename)}")

        except Exception as e:
            print(f"\n从CSV转换为JSON时出错: {e}")

    def update_master_file(self):
        """
        将本次运行的CSV合并到总表 all.csv 中，并根据URL去重。
        """
        print("\n--- 开始更新总表 all.csv ---")

        # 1. 检查本次运行的CSV是否存在
        if not os.path.exists(self.csv_filename):
            print("当前运行的CSV文件不存在，无法更新总表。")
            return

        # 2. 读取新数据
        new_df = pd.read_csv(self.csv_filename)
        if new_df.empty:
            print("新数据为空，无需更新总表。")
            return

        # 3. 读取或创建总表
        if os.path.exists(self.master_filename):
            print(f"读取已有的总表: {self.master_filename}")
            master_df = pd.read_csv(self.master_filename)
        else:
            print("未找到总表，将创建新的 all.csv。")
            master_df = pd.DataFrame()

        # 4. 合并新旧数据
        combined_df = pd.concat([master_df, new_df], ignore_index=True)

        # 5. 根据'URL'列去重，保留最后一次出现的数据（即最新数据）
        #    这可以确保如果职位信息有更新（比如薪资变化），总表里会保留最新的记录
        initial_rows = len(combined_df)
        combined_df.drop_duplicates(subset=["bossURL"], keep="last", inplace=True)
        final_rows = len(combined_df)

        newly_added_rows = final_rows - len(master_df)

        print(f"合并完成：总共 {initial_rows} 条记录，去重后剩余 {final_rows} 条。")
        if newly_added_rows > 0:
            print(f"本次运行新增了 {newly_added_rows} 条独一无二的职位信息。")
        else:
            print("本次运行没有发现新的职位信息。")

        # 6. 保存更新后的总表
        combined_df.to_csv(self.master_filename, index=False, encoding="utf-8-sig")
        print(f"总表已成功保存至: {os.path.abspath(self.master_filename)}")
