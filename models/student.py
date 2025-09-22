"""
学生信息数据模型
"""
import json
from typing import Dict, Any


class StudentDetail:
    """学生详细信息"""
    def __init__(self, detail_data: Dict[str, Any] = None):
        if detail_data:
            self.mz = detail_data.get("mz", "")  # 民族
            self.zjhm = detail_data.get("zjhm", "")  # 证件号码
            self.xz = detail_data.get("xz", "")  # 学制
            self.xljb = detail_data.get("xljb", "")  # 学历级别
            self.fy = detail_data.get("fy", "")  # 分院
            self.xs = detail_data.get("xs", "")  # 系所
            self.bj = detail_data.get("bj", "")  # 班级
            self.xh = detail_data.get("xh", "")  # 学号
            self.rxrq = detail_data.get("rxrq", "")  # 入学日期
            self.yjbyrq = detail_data.get("yjbyrq", "")  # 预计毕业日期
            self.xjzt = detail_data.get("xjzt", "")  # 学籍状态


class Student:
    """学生信息模型"""
    def __init__(self, data: Dict[str, Any]):
        self.photo = data.get("photo", "")
        self.name = data.get("name", "")
        self.sex = data.get("sex", "")
        self.date = data.get("date", "")
        self.school = data.get("school", "")
        self.level = data.get("level", "")
        self.major = data.get("major", "")
        self.rz = data.get("rz", "")  # 入学方式
        self.detail = StudentDetail(data.get("detail", {}))

    @classmethod
    def from_json_file(cls, filepath: str) -> 'Student':
        """从JSON文件加载学生信息"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "photo": self.photo,
            "name": self.name,
            "sex": self.sex,
            "date": self.date,
            "school": self.school,
            "level": self.level,
            "major": self.major,
            "rz": self.rz,
            "detail": {
                "mz": self.detail.mz,
                "zjhm": self.detail.zjhm,
                "xz": self.detail.xz,
                "xljb": self.detail.xljb,
                "fy": self.detail.fy,
                "xs": self.detail.xs,
                "bj": self.detail.bj,
                "xh": self.detail.xh,
                "rxrq": self.detail.rxrq,
                "yjbyrq": self.detail.yjbyrq,
                "xjzt": self.detail.xjzt
            }
        }

    def save_to_file(self, filepath: str) -> None:
        """保存到JSON文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)