import json
import random
import os

from flask import Flask, render_template, request, url_for, redirect, render_template_string

app = Flask(__name__, static_folder='detail_files', static_url_path='/detail_files')


class Data:
    class DataDetail:
        def __init__(self):
            pass
            # self.mz = "汉"
            # self.zjhm = "411502200108019912"
            # self.xz = "3"
            # self.xljb = "普通高等教育"
            # self.fy = "资源环境学院"
            # self.xs = ""
            # self.bj = ""
            # self.xh = "212303020070"
            # self.rxrq = "2023年09月06日"
            # self.yjbyrq = "2026年07月01日"
            # self.xjzt = "在籍（注册学籍）"

    def __init__(self, _d):
        self.detail = Data.DataDetail()
        self.photo = _d["photo"]
        self.name = _d["name"]
        self.sex = _d["sex"]
        self.date = _d["date"]
        self.school = _d["school"]
        self.level = _d["level"]
        self.major = _d["major"]
        self.rz = _d["rz"]
        self.detail.mz = _d["detail"]["mz"]
        self.detail.zjhm = _d["detail"]["zjhm"]
        self.detail.xz = _d["detail"]["xz"]
        self.detail.xljb = _d["detail"]["xljb"]
        self.detail.fy = _d["detail"]["fy"]
        self.detail.xs = _d["detail"]["xs"]
        self.detail.bj = _d["detail"]["bj"]
        self.detail.xh = _d["detail"]["xh"]
        self.detail.rxrq = _d["detail"]["rxrq"]
        self.detail.yjbyrq = _d["detail"]["yjbyrq"]
        self.detail.xjzt = _d["detail"]["xjzt"]

        # self.photo = "https://api.qrtool.cn/?text=https://netcut.cn/ed"
        # self.name = "冯君奭"
        # self.sex = "男"
        # self.date = "2001年08月01日"
        # self.school = "河南理工大学"
        # self.level = "本科"
        # self.major = "地质工程"
        # self.rz = "全日制"
        # self.detail = Data.DataDetail()
        # self.detail.mz = "打不下"
        # self.detail.zjhm = "411502200108019912"
        # self.detail.xz = "3"
        # self.detail.xljb = "普通高等教育"
        # self.detail.fy = "资源环境学院"
        # self.detail.xs = ""
        # self.detail.bj = ""
        # self.detail.xh = "212303020070"
        # self.detail.rxrq = "2023年09月06日"
        # self.detail.yjbyrq = "2026年07月01日"
        # self.detail.xjzt = "在籍（注册学籍）"


@app.route('/d/<short_url>', methods=['GET', 'POST'])
def index(short_url):
    _data = Data(json.load(open(f"detail_files/{short_url}.json", "r", encoding="utf-8")))
    return render_template('detail.html', data=_data)


@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        _data = {
            "photo": request.form.get('photo'),
            "name": request.form.get('name'),
            "sex": request.form.get('sex'),
            "date": request.form.get('date'),
            "school": request.form.get('school'),
            "level": request.form.get('level'),
            "major": request.form.get('major'),
            "rz": request.form.get('rz'),
            "detail": {
                "mz": request.form.get('mz'),
                "zjhm": request.form.get('zjhm'),
                "xz": request.form.get('xz'),
                "xljb": request.form.get('xljb'),
                "fy": request.form.get('fy'),
                "xs": request.form.get('xs'),
                "bj": request.form.get('bj'),
                "xh": request.form.get('xh'),
                "rxrq": request.form.get('rxrq'),
                "yjbyrq": request.form.get('yjbyrq'),
                "xjzt": request.form.get('xjzt')
            }
        }

        # 确保目录存在
        if not os.path.exists('detail_files'):
            os.makedirs('detail_files')

        # 生成唯一ID并保存数据
        _id = random.randint(1000000, 9999999)
        # 确保ID不重复
        while os.path.exists(f"detail_files/{_id}.json"):
            _id = random.randint(1000000, 9999999)

        json.dump(_data, open(f"detail_files/{_id}.json", "w", encoding="utf-8"), ensure_ascii=False)

        # 构建完整的URL
        full_url = request.url_root.rstrip('/') + f'/d/{_id}'

        return render_template('success.html', url=full_url)

    # 默认使用带预览的表单
    return render_template('form_with_preview.html')


if __name__ == '__main__':
    print("注意: main.py 已废弃，建议使用 app.py 运行应用")
    print("正在以兼容模式运行...")
    app.run(debug=True, host="0.0.0.0", port=48088)
