import "antd/dist/reset.css";
import "./styles.css";
import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Alert, Button, Card, Input, Layout, Menu, Modal, Progress, Select, Space, Table, Tabs, Tag, Typography, Upload, message } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import axios from "axios";

const api = axios.create({ baseURL: "/api" });
type Template = { id: number; name: string; has_formula: boolean; sheet_count: number; created_at: string };
type Workflow = { id: number; name: string; mode: string; template_id: number; column_mapping: Record<string, string> };
type DataSource = { id: number; name: string; schema_: Record<string, { type: string }> };
type Task = { id: number; workflow_id: number; data_source_id: number; status: string; error_log?: string; started_at?: string; finished_at?: string };
type PreviewSheet = { title: string; rows: unknown[][] };

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
  const [task, setTask] = useState<Task>();
  const [error, setError] = useState<string>();
  const [preview, setPreview] = useState<PreviewSheet[]>([]);
  const [previewOpen, setPreviewOpen] = useState(false);

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
  const showColumns = async (item: Template) => { setSelected(item); const response = await api.get(`/templates/${item.id}/columns`); setColumns(response.data.sheets?.[0]?.columns ?? []); };
  const showPreview = async (item: Template) => { try { const response = await api.get(`/templates/${item.id}/preview`); setPreview(response.data.sheets); setPreviewOpen(true); } catch (reason) { showError(reason); } };
  const createWorkflow = async () => { if (!selected) return; try { const response = await api.post("/workflows", { template_id: selected.id, name: `${selected.name} 模式A`, mode: "formula" }); setWorkflow(response.data); setMapping({}); setPage("mapping"); await load(); } catch (reason) { showError(reason); } };
  const openWorkflow = async (item: Workflow) => { const template = templates.find((entry) => entry.id === item.template_id); if (template) await showColumns(template); setWorkflow(item); setMapping(item.column_mapping ?? {}); setPage("mapping"); };
  const saveMapping = async () => { if (!workflow) return; try { const response = await api.put(`/workflows/${workflow.id}/mapping`, { column_mapping: mapping }); setWorkflow(response.data); message.success("映射已保存"); } catch (reason) { showError(reason); } };
  const runTask = async () => { if (!workflow || !dataSourceId) return message.warning("请先选择工作流和数据源"); try { const response = await api.post("/tasks/run", { workflow_id: workflow.id, data_source_id: dataSourceId }); setTask(response.data); setPage("tasks"); await load(); } catch (reason) { showError(reason); } };
  const runBatch = async () => { if (!workflow || batchSourceIds.length === 0) return message.warning("请先选择批量数据源"); try { await api.post("/tasks/batch-run", { workflow_id: workflow.id, data_source_ids: batchSourceIds }); message.success(`已提交 ${batchSourceIds.length} 个批量任务`); setPage("history"); await load(); } catch (reason) { showError(reason); } };
  const copyWorkflow = async (item: Workflow) => { try { await api.post(`/workflows/${item.id}/copy`); await load(); message.success("工作流已复制"); } catch (reason) { showError(reason); } };
  const retryTask = async (item: Task) => { try { const response = await api.post(`/tasks/${item.id}/retry`); setTask(response.data); setPage("tasks"); await load(); } catch (reason) { showError(reason); } };

  const fieldOptions = dataSources.flatMap((source) => Object.keys(source.schema_ ?? {}).map((field) => ({ label: field, value: field })));
  const templateColumns = [
    { title: "名称", dataIndex: "name" },
    { title: "公式", render: (_: unknown, item: Template) => item.has_formula ? <Tag color="orange">含公式</Tag> : <Tag>无公式</Tag> },
    { title: "Sheet", dataIndex: "sheet_count" },
    { title: "操作", render: (_: unknown, item: Template) => <Space><Button onClick={() => void showColumns(item)}>查看列</Button><Button onClick={() => void showPreview(item)}>预览</Button><Button type="primary" onClick={() => { void showColumns(item); setPage("mapping"); }}>配置模式 A</Button></Space> },
  ];
  const workflowColumns = [{ title: "名称", dataIndex: "name" }, { title: "操作", render: (_: unknown, item: Workflow) => <Space><Button onClick={() => void openWorkflow(item)}>编辑</Button><Button onClick={() => void copyWorkflow(item)}>复制</Button></Space> }];
  const taskColumns = [{ title: "任务", render: (_: unknown, item: Task) => `#${item.id}` }, { title: "状态", render: (_: unknown, item: Task) => <Tag>{item.status}</Tag> }, { title: "开始", dataIndex: "started_at" }, { title: "完成", dataIndex: "finished_at" }, { title: "操作", render: (_: unknown, item: Task) => <Space>{item.status === "success" && <Button type="link" href={`/api/tasks/${item.id}/download`}>下载</Button>}{["success", "failed"].includes(item.status) && <Button onClick={() => void retryTask(item)}>重试</Button>}</Space> }];
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
      {page === "templates" && <Card title="模板管理" extra={<Upload beforeUpload={(file) => upload("/templates/upload", file)} showUploadList={false}><Button icon={<UploadOutlined />}>上传模板</Button></Upload>}><Table rowKey="id" dataSource={templates} columns={templateColumns} /><Typography.Title level={4}>已保存工作流</Typography.Title><Table rowKey="id" dataSource={workflows} columns={workflowColumns} pagination={false} /><Modal title="模板预览" open={previewOpen} onCancel={() => setPreviewOpen(false)} footer={null} width={900}><Tabs items={previewTabs} /></Modal></Card>}
      {page === "mapping" && <Card title="模式 A 列映射" extra={<Space><Button onClick={() => setPage("templates")}>返回</Button><Button type="primary" onClick={() => void saveMapping()}>保存映射</Button></Space>}>{workflow ? <Table rowKey="column" dataSource={columns} columns={[{ title: "列", dataIndex: "column" }, { title: "表头", dataIndex: "header" }, { title: "类型", dataIndex: "type" }, { title: "数据源字段", render: (_: unknown, item: any) => item.type === "formula" ? <Tag color="orange">自动计算</Tag> : <Select showSearch allowClear value={mapping[item.column]} onChange={(value) => setMapping({ ...mapping, [item.column]: value ?? "" })} options={fieldOptions} placeholder="选择字段" /> }]} /> : <Button type="primary" onClick={() => void createWorkflow()}>创建模式 A 工作流</Button>}</Card>}
      {page === "tasks" && <Card title="任务执行"><Space direction="vertical" size="large" className="wide"><Typography.Text>工作流：{workflow?.name ?? "请先编辑工作流"}</Typography.Text><Upload beforeUpload={(file) => upload("/data-sources/upload", file)} showUploadList={false}><Button icon={<UploadOutlined />}>上传基础数据</Button></Upload><Select value={dataSourceId} onChange={setDataSourceId} placeholder="选择数据源" options={dataSources.map((source) => ({ label: source.name, value: source.id }))} /><Button type="primary" onClick={() => void runTask()}>生成 Excel</Button><Select mode="multiple" value={batchSourceIds} onChange={setBatchSourceIds} placeholder="选择多个数据源批量生成" options={dataSources.map((source) => ({ label: source.name, value: source.id }))} /><Button onClick={() => void runBatch()}>批量生成</Button>{task && <Card size="small" title={`任务 #${task.id}`}><Tag color={task.status === "success" ? "green" : task.status === "failed" ? "red" : "blue"}>{task.status}</Tag>{task.status === "running" && <Progress percent={50} status="active" />}{task.error_log && <Alert message={task.error_log} type="error" />}{task.status === "success" && <Button type="link" href={`/api/tasks/${task.id}/download`}>下载生成文件</Button>}</Card>}</Space></Card>}
      {page === "history" && <Card title="任务历史"><Table rowKey="id" dataSource={tasks} columns={taskColumns} /></Card>}
    </Layout.Content></Layout>
  </Layout>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
