import base64
from pathlib import Path

def encode_file_to_base64_chunks(file_path, output_dir, n_parts, buffer_size=1024*1024):
    """
    数GB級でも安全に分割保存できるストリーム版
    buffer_size: 1MBずつ読み込む
    """
    file_path = Path(file_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    # ファイルサイズ
    total_size = file_path.stat().st_size
    part_size = total_size // n_parts
    remainder = total_size % n_parts

    with open(file_path, "rb") as f:
        for i in range(n_parts):
            # このパートのバイト数
            size_to_read = part_size + (1 if i < remainder else 0)
            out_file = output_dir / f"{file_path.stem}_part{i+1}.txt"
            with open(out_file, "w", encoding="utf-8") as out_f:
                read_bytes = 0
                while read_bytes < size_to_read:
                    chunk = f.read(min(buffer_size, size_to_read - read_bytes))
                    if not chunk:
                        break
                    b64_chunk = base64.b64encode(chunk).decode("utf-8")
                    out_f.write(b64_chunk)
                    read_bytes += len(chunk)
            print(i)

    print(f"ファイルを{n_parts}分割して保存しました: {output_dir}")


def decode_base64_chunks_to_file(input_dir, output_file, file_stem, buffer_size=8192):
    """
    分割されたBase64テキストからストリームで復元
    buffer_size: 読み込む文字数
    """
    input_dir = Path(input_dir)
    chunk_files = sorted(input_dir.glob(f"{file_stem}_part*.txt"))

    with open(output_file, "wb") as out_f:
        for chunk_file in chunk_files:
            with open(chunk_file, "r", encoding="utf-8") as f:
                while True:
                    chunk = f.read(buffer_size)
                    if not chunk:
                        break
                    out_f.write(base64.b64decode(chunk))

    print(f"ファイルを復元しました: {output_file}")


# 使い方例
#decode_base64_chunks_to_file(r"C:\Users\Desktop\test", r"C:\Users\Desktop\restored_sample.mp4", "３項")

# 使い方例
#encode_file_to_base64_chunks(r"C:\Users\Desktop\test\StabilityMatrix-win-x64.zip",r"C:\Users\Desktop\test\barabara", 100)

