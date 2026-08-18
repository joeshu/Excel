# Excel Workflow Platform

Excel 工作流自动生成平台。当前版本采用 Windows 桌面单机架构：pywebview 原生窗口、FastAPI 本地服务、SQLite 本地数据库、进程内后台任务和 React 管理页面，最终可打包为单个 `.exe` 文件。

## 桌面架构

```text
ExcelWorkflow.exe
  ├─ Desktop Shell: pywebview
  │    └─ 创建原生窗口，加载本机动态端口上的 /app
  ├─ Local API: FastAPI + Uvicorn
  │    └─ 提供模板、工作流、数据源、任务和文件下载 API
  ├─ Data: SQLite + data/uploads + data/outputs
  │    └─ 数据和生成文件保存在 exe 同目录，支持长期持久化
  ├─ Worker: ThreadPoolExecutor
  │    └─ 在当前进程中执行 Excel 生成任务
  └─ UI: React + Ant Design
       └─ 构建后作为 exe 内置静态资源由 FastAPI 托管
```

桌面启动时会自动选择空闲本机端口，避免占用 `8000` 产生冲突。服务只监听 `127.0.0.1`，外部设备无法直接访问。关闭窗口会停止 Uvicorn 服务并停止后续任务提交。

Windows 需要安装 Microsoft Edge WebView2 Runtime。Windows 11 通常已经内置，Windows 10 可从微软官方安装 Evergreen Runtime。

## 开发启动

复制环境变量模板：

```bash
cp .env.example .env
```

启动后端：

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端开发服务器：

```bash
cd frontend
npm install
npm run dev
```

访问地址：

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- 前端开发页: http://localhost:5173
- 单机版页面: http://localhost:8000/app

## 项目目录

```text
backend/
  app/
    main.py              FastAPI 入口和健康检查
    config.py            环境配置
    database.py          SQLAlchemy Engine、Session、Base
    models/              五个核心 ORM 模型
    tasks.py             进程内线程池任务执行
  alembic/               数据库迁移脚本
  requirements.txt       Python 依赖
frontend/                React 18 + TypeScript + Vite 基础入口
```

## 数据库模型

初始迁移创建 `templates`、`workflow_defs`、`workflow_nodes`、`data_sources` 和 `task_records` 五张表。桌面版默认使用 SQLite，JSON 字段由 SQLAlchemy 映射为 SQLite 兼容的数据类型。

## Windows 打包

推送到 GitHub 的 `master` 分支后，GitHub Actions 会自动在 Windows runner 上编译 exe。也可以在仓库的 `Actions` 页面手动运行 `Build Windows EXE` workflow。构建完成后，在对应运行记录的 `Artifacts` 区域下载 `ExcelWorkflow-windows-x64`。

在 Windows PowerShell 中执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

脚本会构建 React 前端，将前端产物复制到后端资源目录，使用 PyInstaller 生成 `dist\ExcelWorkflow.exe`。PyInstaller 必须在 Windows 环境执行，Linux 环境无法直接生成 Windows PE 可执行文件。

运行：

```powershell
.\dist\ExcelWorkflow.exe
```

双击 exe 后会直接打开独立的桌面窗口，窗口内就是应用界面。程序不主动打开系统浏览器，关闭桌面窗口会同时退出本地服务。用户数据、上传文件和生成文件会保存在 exe 同目录的 `data` 文件夹中。

## Phase 2 使用流程

1. 在模板管理页上传 `.xlsx` 模板，系统读取第一个 Sheet 的首行列结构并识别公式列。
2. 点击“配置模式 A”，创建公式模板工作流。
3. 在“数据源字段”中填写 CSV/XLSX 表头字段名，公式列保持“自动计算”。
4. 保存映射后进入任务执行页，上传基础数据并点击“生成 Excel”。
5. 通过 Swagger 的 `/api/tasks/{id}/status` 查询执行状态，成功后使用 `/api/tasks/{id}/download` 下载文件。

## 当前能力

- Excel 模板上传和列结构解析
- 模式 A 公式模板工作流
- CSV/XLSX 基础数据上传
- Excel 生成、任务状态查询和结果下载
- Windows 原生桌面窗口运行
- GitHub Actions 自动生成 Windows x64 EXE

## 方案 2 能力

- 多 Sheet 模板解析和预览
- 公式列自动向下填充并使用 `Translator` 调整相对引用
- 模板预览前 20 行数据
- 工作流复制和重新编辑
- 单个数据源生成和多个数据源批量生成
- 任务历史、下载和重试
- VLOOKUP、XLOOKUP、SUMIF、SUMIFS、COUNTIF、COUNTIFS 公式识别和静态校验
- Python 端按条件聚合预览
- 公式引用 Sheet 校验和常见错误值检测
- Windows 优先 Excel COM、无 Excel 时尝试 LibreOffice 的自动重算
- 生成任务支持公式文本、缓存结果和错误状态预览
- 模板公式检查支持直接引用单元格和跨 Sheet 依赖查看
- 数据源支持空值、混合类型质量检查及 Excel 报告下载
- 批量任务支持将成功结果一次性打包为 ZIP 下载
- 模板支持版本号、父模板关联、版本列表查看和新版本上传
- 模式 B 支持 ReactFlow 六类节点编排、DAG 校验、条件过滤、字段计算和模板输出
- 模式 B 节点支持表单化配置，数据源节点可选择实际数据源，字段映射支持按模板表头自动提示
- `sample_data/scenarios/` 提供基础无公式、标准有公式、多 Sheet 复杂公式、异常质量和 CSV 数据源场景
- 应用首次启动会自动将这些场景安装到模板中心、数据源中心和工作流中心，并标记为“示例”
- 修复 Windows EXE 前端资源路径，修复模式 B 数据源一致性、DAG 连通性、CSV 数值公式和节点删除状态问题
- 桌面启动允许 pywebview 在 WebView2 不可用时回退到 Windows MSHTML 渲染器

公式相关接口：

```text
GET /api/formulas/{template_id}/inspect
GET /api/formulas/{template_id}/validate
GET /api/formulas/{template_id}/cached-errors
GET /api/formulas/{template_id}/aggregate?data_source_id=1&group_field=region&value_field=net_amount
```

公式策略：模板中的 `VLOOKUP`、`XLOOKUP`、`SUMIF`、`SUMIFS`、`COUNTIF`、`COUNTIFS`、`IF` 和 `IFERROR` 由 Excel 负责最终计算，平台负责写入数据、复制公式、校验 Sheet 引用并在生成后检查缓存错误值。没有 Excel 计算环境时，聚合类需求可以通过 Python 预览接口提前查看分组数量和合计金额。

运行后端单元测试：

```bash
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

## 复杂样例数据

项目内置一组可重复生成的调测样例：

```bash
python tools/generate_complex_sample.py
```

生成文件：

- `sample_data/complex_source_200x15.xlsx`：200 行、15 列基础数据，包含文本、编号、区域、分类、日期、整数、小数、百分比、缺失值、零数量和备注等场景。
- `sample_data/complex_template_200x15.xlsx`：`销售明细` 和 `汇总` 两个 Sheet，包含金额、折扣、净额、风险等级、`SUMIF`、`COUNTIF`、`IF` 等公式。

调测覆盖：

- 200 行基础数据读取
- 15 列字段映射
- 多 Sheet 模板解析
- 公式自动填充和相对引用转换
- 缺失值与零值数据
- 多 Sheet 输出文件生成
- 公式和样式保留

## 桌面 MVP 范围

当前版本优先落实桌面 MVP：

- 模式 A 模板上传、解析、字段映射和 Excel 生成
- CSV/XLSX 数据源字段选择与运行前校验
- 任务状态自动轮询、失败提示和结果下载
- 任务历史、重试和已保存工作流重新编辑
- SQLite、原生桌面窗口和本地文件持久化

当前版本暂缓：

- 模式 B ReactFlow 可视化设计器
- DAG 节点执行器、条件、循环、转换和合并节点
- PostgreSQL、Redis、Celery、MinIO/S3
- 用户登录、权限、多用户协作和云端部署

这样可以先形成稳定的 Windows 单机 Excel 自动化工具，再根据实际使用反馈扩展模式 B。
