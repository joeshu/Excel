import { Tag } from "antd";

const statusMap: Record<string, { label: string; color: string }> = {
  success: { label: "成功", color: "green" },
  failed: { label: "失败", color: "red" },
  running: { label: "执行中", color: "blue" },
  pending: { label: "排队中", color: "gold" },
  submitted: { label: "已提交", color: "blue" },
};

export function StatusBadge({ status }: { status: string }) {
  const value = statusMap[status] ?? { label: status, color: "default" };
  return <Tag color={value.color}>{value.label}</Tag>;
}
