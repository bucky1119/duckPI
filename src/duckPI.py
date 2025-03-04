import argparse
import subprocess
import pandas as pd
import os

# 获取可执行文件的路径
BIN_DIR = "/storage-01/poultrylab1/csg/duckPI/bin"

# 合并数据函数
def merge_columns(df, new_df, key_cols, new_cols):
    return pd.merge(df, new_df[key_cols + new_cols], on=key_cols, how='left')

# 推断亲缘关系
def infer_relationship(row, metric):
    metric_value = row[metric]
    Z0 = row['Z0']
    if metric_value >= MZ_threshold and Z0 < MZ_π0_threshold:
        return 'MZ'
    elif PO_range[0] < metric_value <= PO_range[1] and Z0 < MZ_π0_threshold:
        return 'PO'
    elif FS_range[0] < metric_value <= FS_range[1] and FS_π0_range[0] <= Z0 <= FS_π0_range[1]:
        return 'FS'
    elif Second_range[0] < metric_value <= Second_range[1] and Second_π0_range[0] <= Z0 <= Second_π0_range[1]:
        return '2nd'
    else:
        return 'UN'

# 命令行参数解析
def parse_args():
    parser = argparse.ArgumentParser(description="Run King and Plink for kinship analysis and merge results.")
    parser.add_argument('--file', type=str, required=True, help="Base filename prefix (without extension).")
    parser.add_argument('--kinship', action='store_true', help="Run kinship analysis using King.")
    parser.add_argument('--out', type=str, required=True, help="Output path for merged results.")
    return parser.parse_args()

# 运行King和Plink的命令
def run_king_and_plink(base_filename):
    # 创建输出目录（如果不存在）
    os.makedirs('./data/King', exist_ok=True)  # 创建King输出目录
    os.makedirs('./data/Plink', exist_ok=True)  # 创建Plink输出目录

    # 获取King和Plink的可执行文件路径
    king_command = f"{BIN_DIR}/king --sexchr 42 -b {base_filename}.bed --kinship --prefix ./data/King/kinship1"
    subprocess.run(king_command, shell=True, check=True)

    plink_command = f"{BIN_DIR}/plink --bfile {base_filename} --genome --chr-set 40 --out ./data/Plink/plink_1"
    subprocess.run(plink_command, shell=True, check=True)

# 合并King和Plink结果
def merge_results(kinship_file, genome_file, output_file):
    kinship_df = pd.read_csv(kinship_file, delim_whitespace=True)
    genome_df = pd.read_csv(genome_file, delim_whitespace=True)
    
    # 合并Kinship数据
    df_merge = merge_columns(df_merge, kinship_df, ['ID1', 'ID2'], ['HetHet','IBS0','Kinship'])
    df_merge['KING'] = df_merge['Kinship'] * 2
    
    # 合并PI_HAT数据
    genome_df.rename(columns={'IID1': 'ID1', 'IID2': 'ID2'}, inplace=True)
    df_merge = merge_columns(df_merge, genome_df, ['ID1', 'ID2'], ['Z0','PI_HAT'])

    # 推断关系并添加到df_merge
    metrics = ['PI_HAT', 'KING']
    for metric in metrics:
        df_merge[f'{metric}_Relation'] = df_merge.apply(lambda row: infer_relationship(row, metric), axis=1)

    # 保存合并后的结果
    df_merge.to_csv(output_file, index=False)

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    
    # 运行King和Plink命令
    run_king_and_plink(args.file)
    
    # 合并结果
    kinship_file = "/storage-01/poultrylab1/csg/duckPI/data/King/kinship1.kin0"  # 更新为实际路径
    genome_file = "/storage-01/poultrylab1/csg/duckPI/data/Plink/plink_1.genome"  # 更新为实际路径
    merge_results(kinship_file, genome_file, args.out)

