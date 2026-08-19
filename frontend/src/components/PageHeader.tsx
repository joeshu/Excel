import { Space, Typography } from "antd";
import type { ReactNode } from "react";

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <div className="page-header"><div><Typography.Text className="page-eyebrow">{eyebrow}</Typography.Text><Typography.Title level={2}>{title}</Typography.Title>{description && <Typography.Paragraph type="secondary">{description}</Typography.Paragraph>}</div>{actions && <Space wrap>{actions}</Space>}</div>;
}
