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

运行后端单元测试：

```bash
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

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
