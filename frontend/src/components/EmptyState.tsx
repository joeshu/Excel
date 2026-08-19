import { Button, Empty, Space, Typography } from "antd";

type EmptyStateProps = {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function EmptyState({ title, description, actionLabel, onAction }: EmptyStateProps) {
  return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<Space direction="vertical" size={4}><Typography.Text strong>{title}</Typography.Text><Typography.Text type="secondary">{description}</Typography.Text>{actionLabel && onAction && <Button type="primary" onClick={onAction}>{actionLabel}</Button>}</Space>} />;
}
