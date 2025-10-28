# duckPI
Pedigree Reconstruction
## 软件说明手册

`./duckPI.py -h`

<img width="656" height="452" alt="image" src="https://github.com/user-attachments/assets/a765408a-fa28-42c9-9b9a-c867517dfa6b" />

**功能1：亲缘关系推断，可以基于Plink与King进行亲缘关系推断**

 `./duckPI.py --file /storage-01/poultrylab1/csg/data/mix/4s3y_711/IndepSNP1 --out df_merge2.csv --kinship`

<img width="615" height="241" alt="image" src="https://github.com/user-attachments/assets/e4a32c66-ada4-440d-bd09-0d8f0a785f96" />


**功能2：系谱构建，可以分别基于King或者Plink的亲缘关系推断结果来构建系谱**

`./duckPI.py  --file df_merge2.csv --extrainfo extra_info.csv --make-king --out king_table`

<img width="846" height="60" alt="image" src="https://github.com/user-attachments/assets/170d2495-563b-4076-b544-fa35fc19f701" />


`./duckPI.py  --file df_merge2.csv --extrainfo extra_info.csv --make-plink --out plink_table`

<img width="845" height="63" alt="image" src="https://github.com/user-attachments/assets/4da30cbd-613b-4274-b08b-9c7c766d1e81" />


<img width="438" height="151" alt="image" src="https://github.com/user-attachments/assets/b45e8292-0e0e-4942-8b85-6d61af95efee" />


**功能3，绘制系谱结果图，输出该个体可能拥有的或属于的最大系谱结构**

`./duckPI.py --pedigree king_table --id NKX06X41X12947 --extrainfo extra_info.csv --draw_pedigree`
<img width="2048" height="65" alt="image" src="https://github.com/user-attachments/assets/4f63e3fd-7ac1-4b33-a215-5b0ca5b5ff64" />
