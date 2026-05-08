# 风雨未至数先知——基于大数据技术的自然灾害可视化预警平台

## 技术栈
- 前端: Vue3 + Vite + ECharts
- 后端: FastAPI
- 大数据: Hadoop(HDFS) + Spark + PySpark + Jupyter

## 目录
- `data/`: 原始 Excel 数据
- `scripts/`: 数据预处理和初始化脚本
- `notebooks/`: Jupyter 分析代码
- `backend/`: API 服务
- `frontend/`: 可视化前端

## 快速启动
1. `docker compose up -d`
2. `pip install -r scripts/requirements.txt`
3. `python scripts/init_hdfs.py`
4. 按 notebook 运行分析生成 `backend/output/analysis_output.json`
5. `uvicorn backend.main:app --reload --port 8000`
6. `cd frontend && npm install && npm run dev`
