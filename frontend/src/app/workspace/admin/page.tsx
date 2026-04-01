"use client";

import { useCallback, useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_BASE_URL ?? "";

type ListResponse<T> = { items?: T[] };

type Organization = {
  id: string;
  name: string;
  code: string;
};

type MatrixRow = {
  user_id: string;
  email: string;
  roles?: string[];
  permissions?: string[];
};

type MatrixResponse = { matrix?: MatrixRow[] };

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!resp.ok) {
    throw new Error(await resp.text());
  }
  return (await resp.json()) as T;
}

export default function AdminPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [roles, setRoles] = useState<unknown[]>([]);
  const [users, setUsers] = useState<unknown[]>([]);
  const [permissions, setPermissions] = useState<unknown[]>([]);
  const [matrix, setMatrix] = useState<MatrixRow[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState("");

  const load = useCallback(
    async (orgId?: string) => {
      const orgResp = await api<ListResponse<Organization>>(
        "/api/admin/organizations",
      );
      const orgs = orgResp.items ?? [];
      setOrganizations(orgs);

      const activeOrg = orgId ?? selectedOrgId ?? orgs[0]?.id;
      if (!activeOrg) return;

      setSelectedOrgId(activeOrg);

      const [rolesResp, usersResp, permissionsResp, matrixResp] =
        await Promise.all([
          api<ListResponse<unknown>>(
            `/api/admin/roles?organization_id=${activeOrg}`,
          ),
          api<ListResponse<unknown>>(
            `/api/admin/users?organization_id=${activeOrg}`,
          ),
          api<ListResponse<unknown>>(`/api/admin/permissions`),
          api<MatrixResponse>(
            `/api/admin/organizations/${activeOrg}/access-matrix`,
          ),
        ]);

      setRoles(rolesResp.items ?? []);
      setUsers(usersResp.items ?? []);
      setPermissions(permissionsResp.items ?? []);
      setMatrix(matrixResp.matrix ?? []);
    },
    [selectedOrgId],
  );

  useEffect(() => {
    load().catch(console.error);
  }, [load]);

  return (
    <div className="space-y-4 p-6">
      <h1 className="text-2xl font-semibold">多租户后台管理</h1>
      <a
        className="text-blue-600 underline"
        href="/docs"
        target="_blank"
        rel="noreferrer"
      >
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
        {organizations.map((org) => (
          <option key={org.id} value={org.id}>
            {org.name}({org.code})
          </option>
        ))}
      </select>

      <section className="rounded border p-4">
        <h2>权限矩阵</h2>
        {matrix.map((row) => (
          <div key={row.user_id} className="border-b py-2 text-sm">
            {row.email} | 角色: {row.roles?.join(",") ?? "-"} | 权限:{" "}
            {row.permissions?.join(",") ?? "-"}
          </div>
        ))}
      </section>
    </div>
  );
}
