import "antd/dist/reset.css";
import "./styles.css";
import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Alert, Button, Card, Input, Layout, Menu, Modal, Progress, Select, Space, Table, Tabs, Tag, Typography, Upload, message } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import axios from "axios";

const api = axios.create({ baseURL: "/api" });
type Template = { id: number; name: string; version: string; parent_template_id?: number; has_formula: boolean; sheet_count: number; created_at: string };
type TemplateVersions = { template_id: number; root_template_id: number; versions: Template[] };
type Workflow = { id: number; name: string; mode: string; template_id: number; column_mapping: Record<string, string> };
type DataSource = { id: number; name: string; schema_: Record<string, { type: string }> };
type Task = { id: number; workflow_id: number; data_source_id: number; status: string; error_log?: string; calculation_engine?: string; started_at?: string; finished_at?: string };
type PreviewSheet = { title: string; rows: unknown[][] };
type FormulaPreview = { formula_count: number; sheets: { title: string; formula_count: number; results: { cell: string; formula: string; value: unknown; error?: string | null }[] }[] };
type FormulaDependencies = { formula_count: number; dependencies: { sheet: string; cell: string; formula: string; references: { sheet: string; cell: string }[] }[] };
type QualityReport = { row_count: number; field_count: number; issue_count: number; valid: boolean; fields: { field: string; rows: number; missing: number; types: string[] }[]; issues: { field: string; type: string; message: string }[] };

function App() {
  const [page, setPage] = useState("templates");
  const [templates, setTemplates] = useState<Template[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selected, setSelected] = useState<Template>();
  const [columns, setColumns] = useState<any[]>([]);
  const [workflow, setWorkflow] = useState<Workflow>();
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [dataSourceId, setDataSourceId] = useState<number>();
  const [batchSourceIds, setBatchSourceIds] = useState<number[]>([]);
  const [batchTaskIds, setBatchTaskIds] = useState<number[]>([]);
  const [task, setTask] = useState<Task>();
  const [error, setError] = useState<string>();
  const [preview, setPreview] = useState<PreviewSheet[]>([]);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [formulaReport, setFormulaReport] = useState<{ formula_count: number; valid: boolean; issues?: { message: string }[] }>();
  const [formulaPreview, setFormulaPreview] = useState<FormulaPreview>();
  const [formulaDependencies, setFormulaDependencies] = useState<FormulaDependencies>();
  const [qualityReport, setQualityReport] = useState<QualityReport>();
  const [templateVersions, setTemplateVersions] = useState<TemplateVersions>();

  const load = async () => {
    const [templatesResponse, workflowsResponse, sourcesResponse, tasksResponse] = await Promise.all([
      api.get<Template[]>("/templates"), api.get<Workflow[]>("/workflows"), api.get<DataSource[]>("/data-sources"), api.get<Task[]>("/tasks"),
    ]);
    setTemplates(templatesResponse.data); setWorkflows(workflowsResponse.data); setDataSources(sourcesResponse.data); setTasks(tasksResponse.data);
  };
  useEffect(() => { void load(); }, []);
  useEffect(() => {
    if (!task || ["success", "failed"].includes(task.status)) return;
    const timer = window.setInterval(async () => {
      const response = await api.get<Task>(`/tasks/${task.id}/status`);
      setTask(response.data);
      if (["success", "failed"].includes(response.data.status)) { window.clearInterval(timer); void load(); }
    }, 1000);
    return () => window.clearInterval(timer);
  }, [task?.id, task?.status]);

  const showError = (reason: unknown) => {
    const detail = axios.isAxiosError(reason) ? reason.response?.data?.detail : "操作失败";
    setError(detail); message.error(detail);
  };
  const upload = async (endpoint: string, file: File) => {
    const body = new FormData(); body.append("file", file);
    try { await api.post(endpoint, body); await load(); message.success("上传成功"); } catch (reason) { showError(reason); }
    return false;
  };
  const uploadTemplate = async (file: File, parent?: Template) => {
    const body = new FormData(); body.append("file", file); body.append("version", parent ? `${Number(parent.version) + 0.1}` : "1.0"); if (parent) body.append("parent_template_id", String(parent.id));
    try { await api.post("/templates/upload", body); await load(); message.success("模板版本上传成功"); } catch (reason) { showError(reason); }
    return false;
  };
  const showColumns = async (item: Template) => {
    setSelected(item);
    const response = await api.get(`/templates/${item.id}/columns`);
    const sheets = response.data.sheets ?? [];
    setColumns(sheets.flatMap((sheet: { title: string; columns: any[] }) => sheet.columns.map((column) => ({ ...column, sheet: sheet.title, mappingKey: `${sheet.title}!${column.column}` }))));
  };
  const showPreview = async (item: Template) => { try { const response = await api.get(`/templates/${item.id}/preview`); setPreview(response.data.sheets); setPreviewOpen(true); } catch (reason) { showError(reason); } };
  const showFormulaReport = async (item: Template) => { try { const [validation, dependencies] = await Promise.all([api.get(`/formulas/${item.id}/validate`), api.get<FormulaDependencies>(`/formulas/${item.id}/dependencies`)]); setFormulaReport(validation.data); setFormulaDependencies(dependencies.data); } catch (reason) { showError(reason); } };
  const createWorkflow = async () => { if (!selected) return; try { const response = await api.post("/workflows", { template_id: selected.id, name: `${selected.name} 模式A`, mode: "formula" }); setWorkflow(response.data); setMapping({}); setPage("mapping"); await load(); } catch (reason) { showError(reason); } };
  const configureTemplate = async (item: Template) => { await showColumns(item); setSelected(item); setWorkflow(undefined); setPage("mapping"); };
  const openWorkflow = async (item: Workflow) => { const template = templates.find((entry) => entry.id === item.template_id); if (template) await showColumns(template); setWorkflow(item); setMapping(item.column_mapping ?? {}); setPage("mapping"); };
  const saveMapping = async () => { if (!workflow) return; try { const response = await api.put(`/workflows/${workflow.id}/mapping`, { column_mapping: mapping }); setWorkflow(response.data); message.success("映射已保存"); } catch (reason) { showError(reason); } };
  const runTask = async () => { if (!workflow || !dataSourceId) return message.warning("请先选择工作流和数据源"); try { const response = await api.post("/tasks/run", { workflow_id: workflow.id, data_source_id: dataSourceId }); setTask(response.data); setPage("tasks"); await load(); } catch (reason) { showError(reason); } };
  const runBatch = async () => { if (!workflow || batchSourceIds.length === 0) return message.warning("请先选择批量数据源"); try { const response = await api.post<{ tasks: { id: number; status: string }[] }>("/tasks/batch-run", { workflow_id: workflow.id, data_source_ids: batchSourceIds }); setBatchTaskIds(response.data.tasks.filter((item) => item.id).map((item) => item.id)); message.success(`已提交 ${batchSourceIds.length} 个批量任务`); setPage("history"); await load(); } catch (reason) { showError(reason); } };
  const copyWorkflow = async (item: Workflow) => { try { await api.post(`/workflows/${item.id}/copy`); await load(); message.success("工作流已复制"); } catch (reason) { showError(reason); } };
  const retryTask = async (item: Task) => { try { const response = await api.post(`/tasks/${item.id}/retry`); setTask(response.data); setPage("tasks"); await load(); } catch (reason) { showError(reason); } };
  const showTaskFormulaPreview = async (item: Task) => { try { const response = await api.get<FormulaPreview>(`/tasks/${item.id}/formula-preview`); setFormulaPreview(response.data); } catch (reason) { showError(reason); } };
  const showQualityReport = async () => { if (!dataSourceId) return message.warning("请先选择数据源"); try { const response = await api.get<QualityReport>(`/data-sources/${dataSourceId}/quality-report`); setQualityReport(response.data); } catch (reason) { showError(reason); } };
  const showVersions = async (item: Template) => { try { const response = await api.get<TemplateVersions>(`/templates/${item.id}/versions`); setTemplateVersions(response.data); } catch (reason) { showError(reason); } };

  const fieldOptions = dataSources.flatMap((source) => Object.keys(source.schema_ ?? {}).map((field) => ({ label: field, value: field })));
  const templateColumns = [
    { title: "名称", dataIndex: "name" },
    { title: "版本", dataIndex: "version" },
    { title: "公式", render: (_: unknown, item: Template) => item.has_formula ? <Tag color="orange">含公式</Tag> : <Tag>无公式</Tag> },
    { title: "Sheet", dataIndex: "sheet_count" },
    { title: "操作", render: (_: unknown, item: Template) => <Space><Button onClick={() => void showColumns(item)}>查看列</Button><Button onClick={() => void showPreview(item)}>预览</Button><Button onClick={() => void showFormulaReport(item)}>公式检查</Button><Button onClick={() => void showVersions(item)}>版本</Button><Upload beforeUpload={(file) => uploadTemplate(file, item)} showUploadList={false}><Button>上传新版本</Button></Upload><Button type="primary" onClick={() => void configureTemplate(item)}>配置模式 A</Button></Space> },
  ];
  const workflowColumns = [{ title: "名称", dataIndex: "name" }, { title: "操作", render: (_: unknown, item: Workflow) => <Space><Button onClick={() => void openWorkflow(item)}>编辑</Button><Button onClick={() => void copyWorkflow(item)}>复制</Button></Space> }];
  const taskColumns = [{ title: "任务", render: (_: unknown, item: Task) => `#${item.id}` }, { title: "状态", render: (_: unknown, item: Task) => <Tag>{item.status}</Tag> }, { title: "计算引擎", dataIndex: "calculation_engine", render: (value: string) => value ?? "未执行" }, { title: "开始", dataIndex: "started_at" }, { title: "完成", dataIndex: "finished_at" }, { title: "操作", render: (_: unknown, item: Task) => <Space>{item.status === "success" && <><Button type="link" href={`/api/tasks/${item.id}/download`}>下载</Button><Button onClick={() => void showTaskFormulaPreview(item)}>公式结果</Button></>}{["success", "failed"].includes(item.status) && <Button onClick={() => void retryTask(item)}>重试</Button>}</Space> }];
  const previewTabs = preview.map((sheet) => {
    const headers = sheet.rows[0] ?? [];
    const rows = sheet.rows.slice(1).map((row, index) => ({ key: index, values: row }));
    const columnsForSheet = headers.map((_header, index) => ({
      title: String(headers[index] ?? `列 ${index + 1}`),
      render: (_: unknown, item: { values: unknown[] }) => String(item.values[index] ?? ""),
    }));
    return { key: sheet.title, label: sheet.title, children: <Table size="small" pagination={false} dataSource={rows} columns={columnsForSheet} /> };
  });

  return <Layout className="shell">
    <Layout.Sider theme="light"><div className="brand">Excel Flow</div><Menu selectedKeys={[page]} onClick={(event) => setPage(event.key)} items={[{ key: "templates", label: "模板管理" }, { key: "mapping", label: "模式 A 映射" }, { key: "tasks", label: "任务执行" }, { key: "history", label: "任务历史" }]} /></Layout.Sider>
    <Layout><Layout.Content className="content"><Typography.Title>Excel 工作流自动生成平台</Typography.Title>{error && <Alert closable message={error} type="error" onClose={() => setError(undefined)} />}
       {page === "templates" && <Card title="模板管理" extra={<Upload beforeUpload={(file) => uploadTemplate(file)} showUploadList={false}><Button icon={<UploadOutlined />}>上传模板</Button></Upload>}><Table rowKey="id" dataSource={templates} columns={templateColumns} /><Typography.Title level={4}>已保存工作流</Typography.Title><Table rowKey="id" dataSource={workflows} columns={workflowColumns} pagination={false} /><Modal title="模板预览" open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={900}><Tabs items={previewTabs} /></Modal><Modal title="模板版本" open={Boolean(templateVersions)} onCancel={() => setTemplateVersions(undefined)} footer={null}><Table rowKey="id" pagination={false} dataSource={templateVersions?.versions ?? []} columns={[{ title: "名称", dataIndex: "name" }, { title: "版本", dataIndex: "version" }, { title: "创建时间", dataIndex: "created_at" }, { title: "公式", render: (_: unknown, item: Template) => item.has_formula ? "含公式" : "无公式" }]} /></Modal><Modal title="公式检查与依赖" open={Boolean(formulaReport)} onCancel={() => { setFormulaReport(undefined); setFormulaDependencies(undefined); }} footer={null} width={1000}><Typography.Paragraph>公式数量：{formulaReport?.formula_count ?? 0}</Typography.Paragraph>{formulaReport?.valid ? <Alert type="success" message="公式引用检查通过" /> : <Alert type="error" message={(formulaReport?.issues ?? []).map((issue) => issue.message).join("；")} />}<Table size="small" pagination={{ pageSize: 10 }} rowKey={(item) => `${item.sheet}!${item.cell}`} dataSource={formulaDependencies?.dependencies ?? []} columns={[{ title: "公式单元格", render: (_: unknown, item: FormulaDependencies["dependencies"][number]) => `${item.sheet}!${item.cell}` }, { title: "公式", dataIndex: "formula" }, { title: "引用单元格", render: (_: unknown, item: FormulaDependencies["dependencies"][number]) => item.references.map((reference) => `${reference.sheet}!${reference.cell}`).join("，") || "无直接引用" }]} /></Modal></Card>}
      {page === "mapping" && <Card title="模式 A 列映射" extra={<Space><Button onClick={() => setPage("templates")}>返回</Button><Button type="primary" onClick={() => void saveMapping()}>保存映射</Button></Space>}>{workflow ? <Table rowKey="mappingKey" dataSource={columns} columns={[{ title: "Sheet", dataIndex: "sheet" }, { title: "列", dataIndex: "column" }, { title: "表头", dataIndex: "header" }, { title: "类型", dataIndex: "type" }, { title: "数据源字段", render: (_: unknown, item: any) => item.type === "formula" ? <Tag color="orange">自动计算</Tag> : <Select showSearch allowClear value={mapping[item.mappingKey]} onChange={(value) => setMapping({ ...mapping, [item.mappingKey]: value ?? "" })} options={fieldOptions} placeholder="选择字段" /> }]} /> : <Button type="primary" onClick={() => void createWorkflow()}>创建模式 A 工作流</Button>}</Card>}
       {page === "tasks" && <Card title="任务执行"><Space direction="vertical" size="large" className="wide"><Typography.Text>工作流：{workflow?.name ?? "请先编辑工作流"}</Typography.Text><Upload beforeUpload={(file) => upload("/data-sources/upload", file)} showUploadList={false}><Button icon={<UploadOutlined />}>上传基础数据</Button></Upload><Space><Select value={dataSourceId} onChange={setDataSourceId} placeholder="选择数据源" options={dataSources.map((source) => ({ label: source.name, value: source.id }))} /><Button onClick={() => void showQualityReport()}>数据质量检查</Button></Space><Button type="primary" onClick={() => void runTask()}>生成 Excel</Button><Select mode="multiple" value={batchSourceIds} onChange={setBatchSourceIds} placeholder="选择多个数据源批量生成" options={dataSources.map((source) => ({ label: source.name, value: source.id }))} /><Button onClick={() => void runBatch()}>批量生成</Button>{task && <Card size="small" title={`任务 #${task.id}`}><Tag color={task.status === "success" ? "green" : task.status === "failed" ? "red" : "blue"}>{task.status}</Tag>{task.calculation_engine && <Typography.Text type="secondary">计算引擎：{task.calculation_engine}</Typography.Text>}{task.status === "running" && <Progress percent={50} status="active" />}{task.error_log && <Alert message={task.error_log} type={task.status === "success" ? "info" : "error"} />}{task.status === "success" && <Button type="link" href={`/api/tasks/${task.id}/download`}>下载生成文件</Button>}</Card>}</Space><Modal title="数据质量报告" open={Boolean(qualityReport)} onCancel={() => setQualityReport(undefined)} footer={qualityReport ? <Button href={`/api/data-sources/${dataSourceId}/quality-report/download`}>下载 Excel 报告</Button> : null} width={900}>{qualityReport && <><Space><Typography.Text>数据行数：{qualityReport.row_count}</Typography.Text><Typography.Text>字段数：{qualityReport.field_count}</Typography.Text><Typography.Text>问题数：{qualityReport.issue_count}</Typography.Text></Space>{qualityReport.valid ? <Alert type="success" message="数据质量检查通过" /> : <Alert type="warning" message="发现数据质量问题，请处理后再生成" />}<Table size="small" pagination={{ pageSize: 10 }} rowKey={(item) => `${item.field}-${item.type}`} dataSource={qualityReport.issues} columns={[{ title: "字段", dataIndex: "field" }, { title: "类型", dataIndex: "type" }, { title: "说明", dataIndex: "message" }]} /></>}</Modal></Card>}
       {page === "history" && <Card title="任务历史" extra={batchTaskIds.length > 0 && <Button type="primary" href={`/api/tasks/batch-download?${batchTaskIds.map((id) => `task_ids=${id}`).join("&")}`}>下载本批次 ZIP</Button>}><Table rowKey="id" dataSource={tasks} columns={taskColumns} /><Modal title="公式结果预览" open={Boolean(formulaPreview)} onCancel={() => setFormulaPreview(undefined)} footer={null} width={1000}><Typography.Paragraph>公式数量：{formulaPreview?.formula_count ?? 0}</Typography.Paragraph><Tabs items={(formulaPreview?.sheets ?? []).map((sheet) => ({ key: sheet.title, label: `${sheet.title} (${sheet.formula_count})`, children: <Table size="small" pagination={{ pageSize: 20 }} rowKey="cell" dataSource={sheet.results} columns={[{ title: "单元格", dataIndex: "cell" }, { title: "公式", dataIndex: "formula" }, { title: "计算值", dataIndex: "value", render: (value: unknown) => String(value ?? "未缓存") }, { title: "错误", dataIndex: "error", render: (value: string | null) => value ? <Tag color="red">{value}</Tag> : <Tag color="green">正常</Tag> }]} /> }))} /></Modal></Card>}
    </Layout.Content></Layout>
  </Layout>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
