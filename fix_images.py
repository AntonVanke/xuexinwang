#!/usr/bin/env python3
"""
修复已上传图片的后缀名问题
Fix extension issues for already uploaded images
"""

import os
import sqlite3
import shutil
from pathlib import Path

def detect_image_type(file_path):
    """通过文件头检测图片类型"""
    with open(file_path, 'rb') as f:
        header = f.read(12)

    if header[:3] == b'\xff\xd8\xff':
        return '.jpg'
    elif header[:8] == b'\x89PNG\r\n\x1a\n':
        return '.png'
    elif header[:4] == b'GIF8':
        return '.gif'
    elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return '.webp'
    elif header[:2] == b'BM':
        return '.bmp'
    else:
        return '.jpg'  # 默认为jpg

def fix_image_extensions():
    """修复uploads目录中所有无后缀名的图片"""
    uploads_dir = 'uploads'

    if not os.path.exists(uploads_dir):
        print(f"目录 {uploads_dir} 不存在")
        return

    fixed_count = 0
    error_count = 0

    # 连接数据库
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    for filename in os.listdir(uploads_dir):
        file_path = os.path.join(uploads_dir, filename)

        # 跳过目录
        if os.path.isdir(file_path):
            continue

        # 检查是否有后缀名
        name, ext = os.path.splitext(filename)
        if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            try:
                # 检测实际文件类型
                real_ext = detect_image_type(file_path)
                new_filename = f"{name}{real_ext}"
                new_file_path = os.path.join(uploads_dir, new_filename)

                # 重命名文件
                shutil.move(file_path, new_file_path)
                print(f"修复: {filename} -> {new_filename}")

                # 更新数据库中的路径
                old_path = f'/uploads/{filename}'
                new_path = f'/uploads/{new_filename}'

                cursor.execute(
                    "UPDATE students SET admission_photo = ? WHERE admission_photo = ?",
                    (new_path, old_path)
                )

                fixed_count += 1

            except Exception as e:
                print(f"错误: 处理 {filename} 时出错: {e}")
                error_count += 1

    # 提交数据库更改
    conn.commit()
    conn.close()

    print(f"\n完成！修复了 {fixed_count} 个文件")
    if error_count > 0:
        print(f"有 {error_count} 个文件处理失败")

def list_problematic_images():
    """列出所有可能有问题的图片"""
    uploads_dir = 'uploads'

    if not os.path.exists(uploads_dir):
        print(f"目录 {uploads_dir} 不存在")
        return

    problematic = []
    for filename in os.listdir(uploads_dir):
        file_path = os.path.join(uploads_dir, filename)

        if os.path.isdir(file_path):
            continue

        name, ext = os.path.splitext(filename)
        if not ext:
            problematic.append(filename)

    if problematic:
        print("发现以下文件没有后缀名:")
        for f in problematic:
            print(f"  - {f}")
        print(f"\n总计: {len(problematic)} 个文件")
    else:
        print("所有文件都有正确的后缀名")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        list_problematic_images()
    else:
        print("开始检查并修复图片后缀名...")
        fix_image_extensions()