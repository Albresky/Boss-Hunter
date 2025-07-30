import os
import pandas as pd
from flask import Flask, jsonify, render_template_string, request, render_template
from config import DATA_DIR, logger
import json
import re

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    """渲染主页面"""
    return render_template("index.html")


@app.route("/api/files")
def list_files():
    """获取数据目录下的所有CSV和JSON文件列表"""
    if not os.path.exists(DATA_DIR):
        return jsonify([])

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(cur_dir, DATA_DIR)

    try:
        files = [
            f for f in os.listdir(data_dir) if f.endswith(".csv") or f.endswith(".json")
        ]
        files.sort(reverse=True)  # 按名称倒序，最新的文件在最前面
        logger.info(f"找到 {len(files)} 个文件: {files}")
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/data/<path:filename>")
def get_file_data(filename):
    """读取指定文件内容并以JSON格式返回"""
    file_path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(file_path)
            # 处理 NaN 值，替换为 None (在JSON中会变为 null)
            df = df.where(pd.notnull(df), None)
            return jsonify(df.to_dict(orient="records"))
        elif filename.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({"error": "Unsupported file type"}), 400
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500


# --- 主程序入口 ---
if __name__ == "__main__":
    # 确保数据目录存在
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"已创建数据目录: {DATA_DIR}")
        # 创建一个示例文件，方便首次运行
        sample_data = [
            {
                "职位名称": "示例职位",
                "薪资": "10-20K",
                "公司": "示例公司",
                "base地点": "北京",
                "工作经验": "1-3年",
                "学历": "本科",
                "福利待遇": "五险一金",
                "领域tag": "示例",
                "职位描述内容": "这是一个示例职位描述。",
                "JD链接": '=HYPERLINK("https://www.zhipin.com", "示例链接")',
            }
        ]
        pd.DataFrame(sample_data).to_csv(
            os.path.join(DATA_DIR, "sample_data.csv"), index=False, encoding="utf-8-sig"
        )
        print(f"已在 {DATA_DIR} 中创建示例文件 'sample_data.csv'")

    # 启动 Flask 应用
    # host='0.0.0.0' 允许局域网内其他设备访问
    app.run(host="0.0.0.0", port=5000, debug=True)
