import { Alert, Button, Form, Input, InputNumber, Modal, Space, Table, Tag, Typography } from "antd";

type SheetAnalysis = { title: string; role_candidates?: { role: string; reason: string }[]; max_row: number; max_column: number; formula_count: number; data_start_row_candidate?: number; field_header_row_candidate?: number; field_headers?: { column: string; header: string }[]; formula_risks?: { type: string; count: number; message: string }[] };
type Analysis = { template_id: number; template_version: string; sheets: SheetAnalysis[]; recommended_profile: Record<string, unknown> };

export function WorkbookProfileModal({ analysis, open, onClose, onSave }: { analysis?: Analysis; open: boolean; onClose: () => void; onSave: (profile: Record<string, unknown>) => void }) {
  const recommended = analysis?.recommended_profile ?? {};
  return <Modal title="工作簿结构分析" open={open} onCancel={onClose} footer={null} width={1000}>
    {analysis && <Space direction="vertical" className="wide">
      <Typography.Text type="secondary">模板版本：{analysis.template_version}</Typography.Text>
      <Table size="small" rowKey="title" pagination={false} dataSource={analysis.sheets} columns={[{ title: "Sheet", dataIndex: "title" }, { title: "行数", dataIndex: "max_row" }, { title: "列数", dataIndex: "max_column" }, { title: "公式", dataIndex: "formula_count" }, { title: "候选角色", render: (_: unknown, item: SheetAnalysis) => item.role_candidates?.map((role) => <Tag key={role.role}>{role.role}</Tag>) }, { title: "数据起始行", dataIndex: "data_start_row_candidate" }]} />
      {analysis.sheets.filter((sheet) => sheet.field_headers?.length).map((sheet) => <Card key={sheet.title} size="small" title={`${sheet.title} 字段契约（表头第 ${sheet.field_header_row_candidate} 行）`}><Space wrap>{sheet.field_headers?.map((field) => <Tag key={field.column}>{field.column} · {field.header}</Tag>)}</Space></Card>)}
      <Alert type="info" message="推荐配置" description={<Form layout="inline" initialValues={{ detail_sheet: recommended.detail_sheet, notice_sheet: recommended.notice_sheet, data_start_row: recommended.data_start_row, style_source_row: recommended.style_source_row }} onFinish={(values) => onSave({ ...values, data_end_rule: "last_nonempty_row", field_contract: recommended.field_contract })}><Form.Item name="notice_sheet" label="通报页"><Input /></Form.Item><Form.Item name="detail_sheet" label="明细页"><Input /></Form.Item><Form.Item name="data_start_row" label="数据起始行"><InputNumber min={1} /></Form.Item><Form.Item name="style_source_row" label="样式来源行"><InputNumber min={1} /></Form.Item><Button type="primary" htmlType="submit">保存模板配置</Button></Form>} />
      <Typography.Text strong>公式风险</Typography.Text>
      {analysis.sheets.flatMap((sheet) => (sheet.formula_risks ?? []).map((risk) => `${sheet.title}：${risk.message}（${risk.count}）`)).map((risk) => <Typography.Text type="warning" key={risk}>{risk}</Typography.Text>)}
    </Space>}
  </Modal>;
}
