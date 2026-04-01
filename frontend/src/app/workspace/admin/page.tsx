"use client";
import { useEffect, useState } from "react";
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_BASE_URL ?? "";
async function api(path: string, init?: RequestInit) {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}
export default function AdminPage() {
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [permissions, setPermissions] = useState<any[]>([]);
  const [matrix, setMatrix] = useState<any[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState("");
  const load = async (orgId?: string) => {
    const orgResp = await api("/api/admin/organizations");
    const orgs = orgResp.items ?? [];
    setOrganizations(orgs);
    const activeOrg = orgId || selectedOrgId || orgs[0]?.id;
    if (!activeOrg) return;
    setSelectedOrgId(activeOrg);
    const [r, u, p, m] = await Promise.all([
      api(`/api/admin/roles?organization_id=${activeOrg}`),
      api(`/api/admin/users?organization_id=${activeOrg}`),
      api(`/api/admin/permissions`),
      api(`/api/admin/organizations/${activeOrg}/access-matrix`),
    ]);
    setRoles(r.items ?? []);
    setUsers(u.items ?? []);
    setPermissions(p.items ?? []);
    setMatrix(m.matrix ?? []);
  };
  useEffect(() => {
    load().catch(console.error);
  }, []);
  return (
    <div className="space-y-4 p-6">
      <h1 className="text-2xl font-semibold">多租户后台管理</h1>
      <a className="text-blue-600 underline" href="/docs" target="_blank">
        打开 API 文档
      </a>
      <div className="rounded border p-4">
        当前组织数: {organizations.length}，角色数: {roles.length}，用户数:{" "}
        {users.length}，权限数: {permissions.length}
      </div>
      <select
        className="rounded border p-2"
        value={selectedOrgId}
        onChange={(e) => load(e.target.value)}
      >
        {organizations.map((o) => (
          <option key={o.id} value={o.id}>
            {o.name}({o.code})
          </option>
        ))}
      </select>
      <section className="rounded border p-4">
        <h2>权限矩阵</h2>
        {matrix.map((row) => (
          <div key={row.user_id} className="border-b py-2 text-sm">
            {row.email} | 角色: {(row.roles || []).join(",") || "-"} | 权限:{" "}
            {(row.permissions || []).join(",") || "-"}
          </div>
        ))}
      </section>
    </div>
  );
}
