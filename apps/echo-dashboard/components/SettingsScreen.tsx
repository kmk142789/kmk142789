'use client';

import { ChangeEvent, useEffect, useMemo, useState } from 'react';
import type { Policy } from '@/lib/types';

interface SettingsScreenProps {
  policy: Policy;
  onUpdatePolicy: (policy: Policy) => Promise<void> | void;
}

export default function SettingsScreen({ policy, onUpdatePolicy }: SettingsScreenProps) {
  const [editMode, setEditMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState<Policy>(policy);

  useEffect(() => {
    setFormData(policy);
  }, [policy]);

  const handleSave = async () => {
    if (saving) {
      return;
    }
    setSaving(true);
    try {
      await onUpdatePolicy(formData);
      setEditMode(false);
    } catch (error) {
      console.error('Failed to update policy', error);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field: keyof Policy, value: number) => {
    setFormData((previous) => ({ ...previous, [field]: value }));
  };

  const formattedPolicyId = useMemo(() => policy.id.replace(/[-_]/g, ' '), [policy.id]);

  return (
    <div className="p-4 pb-20">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-xs uppercase tracking-[0.35em] text-slate-400">{formattedPolicyId}</p>
        </div>
        {!editMode ? (
          <button
            type="button"
            onClick={() => setEditMode(true)}
            className="rounded-lg bg-[#4b7bec] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#3867d6]"
          >
            Edit
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-[#26de81] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#20bf6b] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
        )}
      </div>

      <div className="mb-4 rounded-xl bg-[#252836] p-5 shadow-lg">
        <h2 className="mb-4 font-semibold text-white">Policy Thresholds</h2>

        <PolicyField
          label="Self-Approve Max"
          value={editMode ? formData.selfApproveMax : policy.selfApproveMax}
          onChange={(v) => handleChange('selfApproveMax', v)}
          editMode={editMode}
          description="Maximum amount for single-steward approval"
        />

        <PolicyField
          label="Dual Approve Min"
          value={editMode ? formData.dualApproveMin : policy.dualApproveMin}
          onChange={(v) => handleChange('dualApproveMin', v)}
          editMode={editMode}
          description="Minimum amount requiring two approvals"
        />

        <PolicyField
          label="Governance Min"
          value={editMode ? formData.governanceMin : policy.governanceMin}
          onChange={(v) => handleChange('governanceMin', v)}
          editMode={editMode}
          description="Minimum amount requiring governance vote"
        />

        <PolicyField
          label="Cash Withdrawal Cap"
          value={editMode ? formData.cashWithdrawalCap : policy.cashWithdrawalCap}
          onChange={(v) => handleChange('cashWithdrawalCap', v)}
          editMode={editMode}
          description="Maximum cash withdrawal allowed"
          isLast
        />
      </div>

      <div className="rounded-xl bg-[#252836] p-5 shadow-lg">
        <h2 className="mb-2 font-semibold text-white">About</h2>
        <div className="text-sm text-gray-400">WhisperVault Steward v1.0</div>
        <div className="mt-2 text-xs text-gray-500">Tamper-evident ledger for sovereign trust management</div>
      </div>
    </div>
  );
}

interface PolicyFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  editMode: boolean;
  description: string;
  isLast?: boolean;
}

function PolicyField({ label, value, onChange, editMode, description, isLast = false }: PolicyFieldProps) {
  const formattedValue = useMemo(
    () =>
      new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      }).format(value),
    [value],
  );

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const parsed = Number.parseFloat(event.target.value);
    onChange(Number.isFinite(parsed) ? parsed : 0);
  };

  return (
    <div className={!isLast ? 'mb-4 border-b border-gray-700 pb-4' : undefined}>
      <div className="mb-1 flex items-center justify-between">
        <div className="font-medium text-white">{label}</div>
        {editMode ? (
          <input
            type="number"
            min={0}
            step={50}
            value={Number.isFinite(value) ? value : 0}
            onChange={handleInputChange}
            className="w-32 rounded-lg bg-[#1a1d29] px-3 py-1 text-right text-white focus:outline-none focus:ring-2 focus:ring-[#4b7bec]"
          />
        ) : (
          <div className="font-bold text-[#f7b731]">${formattedValue}</div>
        )}
      </div>
      <div className="text-xs text-gray-400">{description}</div>
    </div>
  );
}
