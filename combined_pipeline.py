import argparse
import re
from pathlib import Path
from typing import Iterable, List

import pandas as pd
from sklearn.preprocessing import StandardScaler

ID_PATTERN = re.compile(r"(?:^|/)[^/]*_F(\d+)_cell_(\d+)\.[^.]+$")


def convert_cell_id(path_text: str) -> str:
    match = ID_PATTERN.search(path_text)
    if not match:
        return path_text
    f_num, c_num = match.groups()
    return f"c_2_{int(f_num)}_{int(c_num)}"


def transform_df(input_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    if df.columns.empty:
        return df

    first_col = df.columns[0]
    if "cell" in df.columns:
        if first_col == "cell":
            df = df.copy()
        else:
            df = df.loc[:, ~df.columns.duplicated()]
    else:
        df = df.rename(columns={first_col: "cell"})
    df["cell"] = df["cell"].astype(str).map(convert_cell_id)
    return df


def resolve_column(df: pd.DataFrame, target: str) -> str:
    lower_map = {c.lower(): c for c in df.columns}
    if target.lower() not in lower_map:
        raise KeyError(f"Missing required column: {target}")
    return lower_map[target.lower()]


def zscore_population(series: pd.Series) -> pd.Series:
    mean = series.mean()
    std = series.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=series.index)
    return (series - mean) / std


def normalize_pc_list(values: Iterable[str]) -> List[str]:
    normalized: List[str] = []
    seen = set()
    for value in values:
        if value is None:
            continue
        for part in str(value).replace(" ", ",").split(","):
            item = part.strip()
            if not item or item in seen:
                continue
            normalized.append(item)
            seen.add(item)
    return normalized


def expand_pc_token(token: str) -> List[str]:
    text = token.strip().upper()
    if not text:
        return []

    if text.startswith("PC"):
        text = text[2:]

    if "-" in text:
        left, right = [part.strip() for part in text.split("-", 1)]
        if left.isdigit() and right.isdigit():
            start = int(left)
            end = int(right)
            if start <= end:
                return [f"PC{i}" for i in range(start, end + 1)]
            return [f"PC{i}" for i in range(start, end - 1, -1)]
        return []

    if text.isdigit():
        return [f"PC{int(text)}"]

    return [f"PC{text}"]


def parse_pc_spec(spec: str) -> List[str]:
    tokens = normalize_pc_list([spec])
    pcs: List[str] = []
    for token in tokens:
        pcs.extend(expand_pc_token(token))
    return pcs


def filter_and_standardize(
    df: pd.DataFrame, id_col: str, pc_names: List[str]
) -> pd.DataFrame:
    resolved_id = resolve_column(df, id_col)
    resolved_pcs = [resolve_column(df, pc) for pc in pc_names]

    columns_to_keep = [resolved_id] + resolved_pcs
    filtered = df[columns_to_keep].copy()

    scaler = StandardScaler()
    filtered[resolved_pcs] = scaler.fit_transform(filtered[resolved_pcs])
    return filtered


def apply_abs_and_zscore(df: pd.DataFrame, abs_pcs: List[str]) -> pd.DataFrame:
    if not abs_pcs:
        return df

    out = df.copy()
    for pc in abs_pcs:
        col = resolve_column(out, pc)
        out[col] = zscore_population(out[col].abs())
    return out


def resolve_path(path_text: str, base_dir: Path) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = base_dir / path
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline: transformed_matrix_modified -> 标准化 PC1-6 -> 取绝对值后再标准化"
    )
    parser.add_argument(
        "--input",
        default="transformed_matrix.csv",
        help="输入 transformed_matrix.csv 路径（默认: transformed_matrix.csv）",
    )
    parser.add_argument(
        "--output",
        default="standardized_PC1_to_PC6_absolute.csv",
        help="步骤3输出路径（默认: standardized_PC1_to_PC6_absolute.csv）",
    )
    parser.add_argument(
        "--id-col",
        default="cell",
        help="标识列名（默认: cell）",
    )
    parser.add_argument(
        "--pcs",
        default="PC1-6",
        help="需要保留并标准化的 PC 列（例如: PC1-6 或 1,2,3）",
    )
    parser.add_argument(
        "--abs-pcs",
        default="",
        help="需要取绝对值并再标准化的 PC 列（例如: PC3,PC4 或 3 4）",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互式输入 PC 范围和取绝对值的 PC",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent

    input_path = resolve_path(args.input, base_dir)
    output_path = resolve_path(args.output, base_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    if args.interactive:
        pcs_input = input("请输入保留并标准化的 PC 范围（如 PC1-6 或 1,2,3）: ").strip()
        if pcs_input:
            args.pcs = pcs_input
        abs_input = input("请输入需要取绝对值的 PC（如 PC3,PC4 或 3 4），留空表示不取绝对值: ").strip()
        if abs_input:
            args.abs_pcs = abs_input
        else:
            args.abs_pcs = ""

    df_modified = transform_df(input_path)
    pc_list = parse_pc_spec(args.pcs)
    if not pc_list:
        raise SystemExit("未解析到任何 PC 列，请检查 --pcs 参数是否正确。")
    df_standardized = filter_and_standardize(df_modified, args.id_col, pc_list)

    abs_pc_list = parse_pc_spec(args.abs_pcs)
    df_final = apply_abs_and_zscore(df_standardized, abs_pc_list)
    df_final.to_csv(output_path, index=False)

    print(f"步骤3输出: {output_path}")
    print("处理完成")


if __name__ == "__main__":
    main()
