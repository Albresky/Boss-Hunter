import pandas as pd
import sys

def convert_csv_to_json(csv_filename: str, json_filename: str):
    df = pd.read_csv(csv_filename)
    df.to_json(json_filename, orient="records", lines=True, force_ascii=False)
    print(f"已将CSV文件 '{csv_filename}' 转换为JSON文件 '{json_filename}'。")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 2:
        print("用法: python csv2json.py <csv_filename> <json_filename>")
    else:
        csv_file = args[0]
        json_file = args[1]
        convert_csv_to_json(csv_file, json_file)
        print(f"转换完成: {csv_file} -> {json_file}")
