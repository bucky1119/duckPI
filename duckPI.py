#!/usr/bin/env python3

import os
import subprocess
import argparse
import pandas as pd
from graphviz import Digraph
import networkx as nx

# 获取当前工作目录
CURRENT_DIR = os.getcwd()

# 假设 KING 和 Plink 位于当前目录下的 bin 目录
KING_PATH = os.path.join(CURRENT_DIR, 'bin', 'king')
PLINK_PATH = os.path.join(CURRENT_DIR, 'bin', 'plink')

# 定义常量值
MZ_phi = 1
PO_phi = 1 / 2
FS_phi = 1 / 2
Second_phi = 1 / 4
UN_phi = 0
MZ_π0_threshold = 0.1
FS_π0_range = (0.1, 0.365)
Second_π0_range = (0.365, 1 - 1 / (2 ** (3 / 2)))
# 定义指标的阈值范围
MZ_threshold = 1 / (2 ** (1 / 2))
PO_range = (1 / (2 ** (3 / 2)), 1 / (2 ** (1 / 2)))
FS_range = (1 / (2 ** (3 / 2)), 1 / (2 ** (1 / 2)))
Second_range = (1 / (2 ** (5 / 2)), 1 / (2 ** (3 / 2)))

# 命令行参数解析
def parse_args():
    parser = argparse.ArgumentParser(description="Run King and Plink for kinship analysis and merge results.")
    parser.add_argument('--kinship', action='store_true', help="基于KING与plink实现亲缘关系推断")
    parser.add_argument('--id', type=str, help="基于目标ID的系谱重构.")
    parser.add_argument('--pedigree', type=str, help="Pedigree file for visualization.")
    parser.add_argument('--draw_pedigree', action='store_true', help="Draw pedigree graph.")
    # 系谱构建相关参数
    parser.add_argument('--file', type=str, help="输入数据文件路径")
    parser.add_argument('--extrainfo', type=str, help="包含世代和性别信息的文件路径")
    # KING 和 PLINK分析相关参数
    parser.add_argument('--make-king', action='store_true', help="使用King进行亲缘关系推断")
    parser.add_argument('--make-plink', action='store_true', help="使用Plink进行亲缘关系推断")
    # 输出路径
    parser.add_argument('--out', type=str, help="输出文件路径")
    return parser.parse_args()

# 功能1：推断亲缘关系
# 运行King和Plink的命令
def run_king_and_plink(base_filename):
    os.makedirs('./data/King', exist_ok=True)  # 创建King输出目录
    os.makedirs('./data/Plink', exist_ok=True)  # 创建Plink输出目录
    king_command = f"{KING_PATH} --sexchr 42 -b {base_filename}.bed --kinship --prefix ./data/King/kinship1"
    subprocess.run(king_command, shell=True, check=True)
    plink_command = f"{PLINK_PATH} --bfile {base_filename} --genome --chr-set 40 --out ./data/Plink/plink_1"
    subprocess.run(plink_command, shell=True, check=True)
# 合并数据函数
def merge_columns(df, new_df, key_cols, new_cols):
    return pd.merge(df, new_df[key_cols + new_cols], on=key_cols, how='left')
# 合并结果
def merge_results(kinship_file, genome_file, output_file):
    kinship_df = pd.read_csv(kinship_file, delim_whitespace=True)
    genome_df = pd.read_csv(genome_file, delim_whitespace=True)
    df_merge = pd.DataFrame()
    df_merge = kinship_df[['ID1', 'ID2', 'Kinship']]
    df_merge.loc[:, 'KING'] = df_merge['Kinship'] * 2
    genome_df.rename(columns={'IID1': 'ID1', 'IID2': 'ID2'}, inplace=True)
    df_merge = merge_columns(df_merge, genome_df, ['ID1', 'ID2'], ['Z0','PI_HAT'])
    #metrics = ['PI_HAT','KING']
    #df_merge[f'{metric}_Relation'] = df_merge.apply(lambda row: infer_relationship(row, metric), axis=1)
    metrics = ['PI_HAT','KING']
    for metric in metrics:
        df_merge[f'{metric}_Relation'] = df_merge.apply(lambda row: infer_relationship(row, metric), axis=1)
    df_merge.to_csv(output_file, index=False,sep='\t')
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

# 功能2: 基于King或者Plink的系谱重构
def run_pedigree_construction(args):
    # 读取输入数据
    df_merge = pd.read_csv(args.file, sep='\t')  # 输入的亲缘关系数据
    extra_info = pd.read_csv(args.extrainfo, sep='\t')  # 补充的世代与性别信息

    # 检查使用 KING 或 PLINK 的关系推断结果
    relation_column = 'KING_Relation' if args.make_king else 'PI_HAT_Relation'

    if relation_column not in df_merge.columns:
        raise ValueError(f"Column '{relation_column}' not found in input file {args.file}.")

    # 获取所有非最大世代的个体ID
    min_generation = extra_info['Generation'].min()
    other_generations = extra_info[extra_info['Generation'] != min_generation]['ID']

    # 创建一个字典来存储每个个体的父母信息
    parents_dict = {}

    # 筛选出稳健的 PO 关系
    po_df = df_merge[df_merge[relation_column] == 'PO']

    # 对于 other_generations 中的每个个体 ID，查找其父母
    for child_id in other_generations:
        # 获取与子代相关的 PO 关系数据
        potential_parents = po_df[(po_df['ID1'] == child_id) | (po_df['ID2'] == child_id)]

        # 如果找到了父母候选人
        if not potential_parents.empty:
            father_id = None
            mother_id = None

            # 遍历每个父母候选人
            for _, row in potential_parents.iterrows():
                # 判断哪个是父母
                parent_id = row['ID1'] if row['ID2'] == child_id else row['ID2']
                
                # 获取父母的性别和世代信息
                parent_row = extra_info[extra_info['ID'] == parent_id].iloc[0]
                parent_generation = parent_row['Generation']
                parent_gender = parent_row['Sex']
                
                # 判断父母性别和世代
                if parent_generation < extra_info[extra_info['ID'] == child_id]['Generation'].iloc[0]:
                    # 世代小的是父母
                    if parent_gender == 1 and father_id is None:
                        father_id = parent_id
                    elif parent_gender == 2 and mother_id is None:
                        mother_id = parent_id

            # 如果没有找到父母，设置为 None
            if father_id is None or mother_id is None:
                father_id = mother_id = None

            # 将结果存储在字典中
            parents_dict[child_id] = {'父亲ID': father_id, '母亲ID': mother_id}

    # 将父母信息转换为DataFrame
    parents_df = pd.DataFrame.from_dict(parents_dict, orient='index').reset_index()
    parents_df.columns = ['子代ID', '父亲ID', '母亲ID']

    # 保存系谱表到指定的输出文件
    parents_df.to_csv(args.out, index=False, sep='\t')
    print(f"Pedigree construction complete. Output saved to {args.out}")

# 功能3：绘制系谱图
def build_and_draw_pedigree_graph(pedigree_df, extra_info, target_id, output_file='pedigree_picture'):
    G = nx.Graph()
    for _, row in pedigree_df.iterrows():
        child_id = row['子代ID']
        father_id = row['父亲ID']
        mother_id = row['母亲ID']
        if pd.notna(father_id) and pd.notna(child_id):
            G.add_edge(father_id, child_id)
        if pd.notna(mother_id) and pd.notna(child_id):
            G.add_edge(mother_id, child_id)
    #获取目标个体所在的最大连通子图
    subgraph_nodes = nx.node_connected_component(G, target_id)
    ## 从家系图中提取该连通子图
    subgraph = G.subgraph(subgraph_nodes)
    #获取世代和性别信息
    generation_dict = extra_info.set_index('ID')['Generation'].to_dict()
    sex_dict = extra_info.set_index('ID')['Sex'].to_dict()
    ## 使用Graphviz创建图形
    dot = Digraph(format='png', engine='dot')
    dot.attr(dpi='300', rankdir='TB', style='solid', labelloc='t')
    ## 按世代排列节点（父母世代放在上面，子代放在下面）
    generation_nodes = {}
    for node in subgraph.nodes:
        gen = generation_dict.get(node, 0)
        if gen not in generation_nodes:
            generation_nodes[gen] = []
        generation_nodes[gen].append(node)

    for gen in sorted(generation_nodes.keys(), reverse=True):
        with dot.subgraph() as s:
            s.attr(rank='same')
            for node in generation_nodes[gen]:
                s.node(node)

    for node in subgraph.nodes:
        if node == target_id:# # 标记目标个体为红色，其他节点按性别区分形状
            sex = sex_dict.get(node, 0)
            if sex == 1:
                dot.node(node, shape='box', label=node, color='red')
            elif sex == 2:
                dot.node(node, shape='ellipse', label=node, color='red')
        else:## 根据性别设置形状：性别为1为方框，性别为2为圆形
            sex = sex_dict.get(node, 0)
            if sex == 1:# 性别为1，方框,公
                dot.node(node, shape='box', label=node, color='black')
            elif sex == 2:# 性别为2，圆形,母
                dot.node(node, shape='ellipse', label=node, color='black')
    # 遍历边，添加有向边（父母->子代），根据世代信息判断边的方向
    for u, v in subgraph.edges:
        u_gen = generation_dict.get(u, 0)
        v_gen = generation_dict.get(v, 0)

        # 如果父母世代较小，箭头从父母指向子代
        if u_gen < v_gen:  # u 是父母，v 是子代
            dot.edge(u, v, dir='forward')
        else:  # u 是子代，v 是父母
            dot.edge(v, u, dir='forward')
    dot.render(output_file)

if __name__ == "__main__":
    args = parse_args()
     # 功能1：如果没有绘制系谱图，默认运行 KING 和 PLINK 分析
    if args.kinship:
        # 执行 KING 和 PLINK 分析
        if args.file:
            run_king_and_plink(args.file)

            # 假设kinship_file和genome_file是预定义的路径，这里可以根据需求修改
            kinship_file = "./data/King/kinship1.kin0"
            genome_file = "./data/Plink/plink_1.genome"

            # 合并KING和PLINK分析结果
            merge_results(kinship_file, genome_file, args.out)
        else:
            print("Please provide a valid file path using --file for kinship analysis.")
            
    # 功能2：处理构建系谱的功能（--make-king 或 --make-plink）
    if args.make_king or args.make_plink:
        if args.file and args.extrainfo:
            # 如果需要运行 King 或 Plink 来生成系谱
            run_pedigree_construction(args)
        else:
            print("Please provide both --file kinship analysis results and --extrainfo for Pedigree Reconstruction.")
        
    # 功能3：处理绘制系谱图的功能（--draw_pedigree）
    if args.draw_pedigree:
        # 如果需要绘制系谱图，确保传入了 --id 和 --pedigree 参数
        if args.id and args.pedigree:
            # 加载系谱数据和额外信息（性别和世代）
            pedigree_df = pd.read_csv(args.pedigree, sep='\t')
            extra_info = pd.read_csv(args.extrainfo,sep='\t') if args.extrainfo else pd.DataFrame(columns=["ID", "Sex", "Generation"])

            # 调用函数绘制系谱图
            build_and_draw_pedigree_graph(pedigree_df, extra_info, args.id, output_file=f"pedigree_{args.id}")
        else:
            print("Please provide both --id and --pedigree for drawing the pedigree.")
    
   


