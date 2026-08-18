import "antd/dist/reset.css";
import "./styles.css";
import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Button, Card, Input, Layout, Menu, Space, Table, Tag, Typography, Upload, message } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import axios from "axios";

const api = axios.create({ baseURL: "/api" });

type Template = { id: number; name: string; has_formula: boolean; sheet_count: number; created_at: string };
type Workflow = { id: number; name: string; mode: string; template_id: number; column_mapping: Record<string, string> };

function App() {
  const [page, setPage] = useState("templates");
  const [templates, setTemplates] = useState<Template[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selected, setSelected] = useState<Template>();
  const [columns, setColumns] = useState<any[]>([]);
  const [workflow, setWorkflow] = useState<Workflow>();
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [dataSourceId, setDataSourceId] = useState<number>();
  const [task, setTask] = useState<any>();

  const loadTemplates = () => api.get<Template[]>("/templates").then((response) => setTemplates(response.data));
  const loadWorkflows = () => api.get<Workflow[]>("/workflows").then((response) => setWorkflows(response.data));
  useEffect(() => { void loadTemplates(); void loadWorkflows(); }, []);

  const uploadTemplate = async (file: File) => {
    const body = new FormData(); body.append("file", file);
    await api.post("/templates/upload", body); message.success("模板上传成功"); await loadTemplates(); return false;
  };
  const uploadData = async (file: File) => {
    const body = new FormData(); body.append("file", file);
    const response = await api.post("/data-sources/upload", body); setDataSourceId(response.data.id); message.success("基础数据上传成功"); return false;
  };
  const showColumns = async (item: Template) => { setSelected(item); const response = await api.get(`/templates/${item.id}/columns`); setColumns(response.data.sheets?.[0]?.columns ?? []); };
  const createFormulaWorkflow = async () => { if (!selected) return; const response = await api.post("/workflows", { template_id: selected.id, name: `${selected.name} 模式A`, mode: "formula" }); setWorkflow(response.data); setMapping({}); setPage("mapping"); await loadWorkflows(); };
  const saveMapping = async () => { if (!workflow) return; const response = await api.put(`/workflows/${workflow.id}/mapping`, { column_mapping: mapping }); setWorkflow(response.data); message.success("列映射已保存"); };
  const runTask = async () => { if (!workflow || !dataSourceId) return message.warning("请先选择工作流并上传数据"); const response = await api.post("/tasks/run", { workflow_id: workflow.id, data_source_id: dataSourceId }); setTask(response.data); setPage("tasks"); };

  return <Layout className="shell"><Layout.Sider theme="light"><div className="brand">Excel Flow</div><Menu selectedKeys={[page]} onClick={(event) => setPage(event.key)} items={[{ key: "templates", label: "模板管理" }, { key: "mapping", label: "模式 A 映射" }, { key: "tasks", label: "任务执行" }]} /></Layout.Sider><Layout><Layout.Content className="content"><Typography.Title>Excel 工作流自动生成平台</Typography.Title>{page === "templates" && <Card title="模板管理" extra={<Upload beforeUpload={uploadTemplate} showUploadList={false}><Button icon={<UploadOutlined />}>上传 .xlsx 模板</Button></Upload>}><Table rowKey="id" dataSource={templates} columns={[{ title: "名称", dataIndex: "name" }, { title: "公式", render: (_: unknown, item: Template) => item.has_formula ? <Tag color="orange">含公式</Tag> : <Tag>无公式</Tag> }, { title: "Sheet 数", dataIndex: "sheet_count" }, { title: "创建时间", dataIndex: "created_at" }, { title: "操作", render: (_: unknown, item: Template) => <Space><Button onClick={() => void showColumns(item)}>查看列</Button><Button type="primary" onClick={() => { void showColumns(item); setPage("mapping"); }}>配置模式 A</Button></Space> }]} /></Card>}{page === "mapping" && <Card title="模式 A 列映射" extra={<Space><Button onClick={() => setPage("templates")}>返回模板</Button><Button type="primary" onClick={() => void saveMapping()}>保存映射</Button></Space>}>{workflow ? <Table rowKey="column" dataSource={columns} columns={[{ title: "列", dataIndex: "column" }, { title: "表头", dataIndex: "header" }, { title: "类型", dataIndex: "type" }, { title: "数据源字段", render: (_: unknown, item: any) => item.type === "formula" ? <Tag color="orange">自动计算</Tag> : <Input value={mapping[item.column]} onChange={(event) => setMapping({ ...mapping, [item.column]: event.target.value })} placeholder="例如 name" /> }]} /> : <Button type="primary" onClick={() => void createFormulaWorkflow()}>为当前模板创建模式 A 工作流</Button>}</Card>}{page === "tasks" && <Card title="任务执行"><Space direction="vertical" size="large" className="wide"><Typography.Text>工作流：{workflow?.name ?? "请从映射页选择或创建"}</Typography.Text><Upload beforeUpload={uploadData} showUploadList={false}><Button icon={<UploadOutlined />}>上传基础数据 CSV / XLSX</Button></Upload><Button type="primary" onClick={() => void runTask()}>生成 Excel</Button>{task && <Typography.Paragraph>任务 #{task.id} 已提交，状态：{task.status}</Typography.Paragraph>}</Space></Card>}</Layout.Content></Layout></Layout>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
