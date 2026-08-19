import { Form, Input, InputNumber, Modal, Select, Space, Typography } from "antd";

export type NoticeMetricConfig = {
  column: string;
  source_field: string;
  aggregate: string;
  dimension_field?: string;
  filters?: { field: string; operator: string; value: string }[];
};

export type NoticeWorkflowConfig = {
  dimensions: { source_field?: string; rule_field?: string; rule_value?: string };
  rows: { row: number; key: string; aliases?: string[] }[];
  metrics: Record<string, NoticeMetricConfig>;
  totals: Record<string, { operation: string }>;
  execution_mode: "value" | "formula";
};

type Props = {
  open: boolean;
  config?: NoticeWorkflowConfig;
  onCancel: () => void;
  onSave: (config: NoticeWorkflowConfig) => void;
  onPreview?: () => void;
  onHistory?: () => void;
};

const fallback: NoticeWorkflowConfig = {
  dimensions: { source_field: "BA", rule_field: "AZ", rule_value: "发展人" },
  rows: [{ row: 5, key: "" }],
  metrics: { daily: { column: "E", source_field: "W", aggregate: "sum", dimension_field: "BA" } },
  totals: {},
  execution_mode: "value",
};

export function NoticeWorkflowConfigModal({ open, config, onCancel, onSave, onPreview, onHistory }: Props) {
  const [form] = Form.useForm<NoticeWorkflowConfig>();
  const initial = config ?? fallback;
  return <Modal title="编辑模板原生通报配置" open={open} onCancel={onCancel} okText="保存新版本" onOk={() => void form.validateFields().then(onSave)} width={900} destroyOnClose>
    <Typography.Paragraph type="secondary">配置会保存为新的工作流版本，历史版本继续保留。当前模板原生通报使用 BA 作为组织字段、AZ 作为规则字段。</Typography.Paragraph>
    <Form form={form} layout="vertical" initialValues={initial}>
      <Space className="wide" wrap><button type="button" className="ant-btn" onClick={onPreview}>预览当前数据</button><button type="button" className="ant-btn" onClick={onHistory}>查看配置历史</button></Space>
      <Space wrap className="wide">
        <Form.Item label="组织字段" name={["dimensions", "source_field"]} rules={[{ required: true }]}><Select style={{ width: 220 }} options={[{ label: "BA · 下沉区县名称", value: "BA" }, { label: "H · 收入归属区县名称", value: "H" }, { label: "AG · 受理渠道区县名称", value: "AG" }]} /></Form.Item>
        <Form.Item label="规则字段" name={["dimensions", "rule_field"]}><Select style={{ width: 180 }} options={[{ label: "AZ · 下沉规则", value: "AZ" }]} /></Form.Item>
        <Form.Item label="规则值" name={["dimensions", "rule_value"]}><Input placeholder="例如：发展人" /></Form.Item>
      </Space>
      <Form.List name="rows">
        {(fields) => <><Typography.Text strong>通报组织行</Typography.Text>{fields.map((field) => <Space key={field.key} align="baseline" wrap><Form.Item {...field} name={[field.name, "row"]} label="行号" rules={[{ required: true }]}><InputNumber min={1} /></Form.Item><Form.Item {...field} name={[field.name, "key"]} label="组织名称" rules={[{ required: true }]}><Input placeholder="例如：邓州或南阳市邓州市分公司" /></Form.Item></Space>)}</>}
      </Form.List>
      <Typography.Text strong>指标配置 E:L</Typography.Text>
      {[["daily", "E", "基础指标"], ["daily_rate", "F", "日完成率"], ["original", "G", "原数量"], ["final", "H", "最终数量"], ["sequential_rate", "I", "序时完成率"], ["rank", "J", "排名"], ["product_daily", "K", "分产品日"], ["product_monthly", "L", "分产品月"]].map(([name, column, label]) => <Space key={name} wrap className="wide metric-config-row"><Form.Item label={`${label} 指标名`} name={["metrics", name, "label"]}><Input placeholder={String(name)} /></Form.Item><Form.Item label="列" name={["metrics", name, "column"]} initialValue={column}><Input /></Form.Item><Form.Item label="来源字段" name={["metrics", name, "source_field"]}><Input placeholder="W" /></Form.Item><Form.Item label="聚合" name={["metrics", name, "aggregate"]} initialValue="sum"><Select style={{ width: 130 }} options={["sum", "count", "count_distinct", "avg", "max"].map((value) => ({ label: value, value }))} /></Form.Item><Form.Item label="维度字段" name={["metrics", name, "dimension_field"]} initialValue="BA"><Input placeholder="BA" /></Form.Item></Space>)}
      <Form.Item label="执行模式" name="execution_mode"><Select options={[{ label: "值计算（推荐）", value: "value" }, { label: "Excel 公式（待重算）", value: "formula" }]} /></Form.Item>
    </Form>
  </Modal>;
}
