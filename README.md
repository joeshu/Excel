# Excel Workflow Platform

Excel 工作流自动生成平台。当前版本支持 Windows 单机运行：SQLite 本地数据库、进程内后台任务、FastAPI 服务和 React 管理页面，最终可打包为单个 `.exe` 文件。

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

## Phase 1 目录

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

初始迁移创建 `templates`、`workflow_defs`、`workflow_nodes`、`data_sources` 和 `task_records` 五张表。JSON 字段使用 PostgreSQL 原生 JSON 类型保存模板列元数据、工作流节点配置、列映射和数据源配置。

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

然后打开 `http://127.0.0.1:8000/app`。用户数据、上传文件和生成文件会保存在 exe 同目录的 `data` 文件夹中。

## Phase 2 使用流程

1. 在模板管理页上传 `.xlsx` 模板，系统读取第一个 Sheet 的首行列结构并识别公式列。
2. 点击“配置模式 A”，创建公式模板工作流。
3. 在“数据源字段”中填写 CSV/XLSX 表头字段名，公式列保持“自动计算”。
4. 保存映射后进入任务执行页，上传基础数据并点击“生成 Excel”。
5. 通过 Swagger 的 `/api/tasks/{id}/status` 查询执行状态，成功后使用 `/api/tasks/{id}/download` 下载文件。

## 下一阶段

Phase 2 将增加 Excel 模板上传解析、模式 A 列映射、任务执行接口以及模板管理和任务执行页面。
