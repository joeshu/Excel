import { Alert, Card, Progress, Space, Tag, Typography } from "antd";

type Props = { configured: boolean; version?: number; executionMode?: string };

export function NativeWorkflowImprovements({ configured, version, executionMode }: Props) {
  const items = [
    { label: "模板结构契约", done: configured, detail: "Sheet、表头、数据起始行和样式来源" },
    { label: "组织与规则映射", done: configured, detail: "BA 下沉区县名称与可选 AZ 规则" },
    { label: "E:L 指标口径", done: configured, detail: "聚合、比率、排名、日月周期" },
    { label: "值版与公式版对照", done: executionMode === "formula", detail: "预期值、公式文本和 Excel 重算" },
  ];
  const done = items.filter((item) => item.done).length;
  return <Card className="native-improvements" title={<div><Typography.Text className="card-kicker">NATIVE REPORT ROADMAP</Typography.Text><Typography.Title level={4}>模板原生通报提升空间</Typography.Title></div>} extra={<Tag color={done === items.length ? "green" : "gold"}>配置版本 {version ?? "草稿"}</Tag>}><Alert type="info" showIcon message="当前模式可以持续演进" description="后续换通报样式时重新分析模板，换基础数据时重新确认字段契约，工作流历史版本保持可追溯。" /><Progress percent={Math.round(done / items.length * 100)} format={() => `${done}/${items.length} 已完成`} /><div className="native-improvement-list">{items.map((item) => <div key={item.label} className={item.done ? "is-done" : ""}><span className="improvement-dot" /> <div><Typography.Text strong>{item.label}</Typography.Text><Typography.Text type="secondary">{item.detail}</Typography.Text></div></div>)}</div></Card>;
}
