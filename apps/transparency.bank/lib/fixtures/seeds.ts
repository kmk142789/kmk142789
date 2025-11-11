import { Wallet, SpendRequest, LedgerEntry, Policy, Snapshot } from "../types";

export const seedWallets: Wallet[] = [
  {
    id: "w1",
    chain: "Ethereum",
    address: "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    label: "Main Treasury",
    verified: true,
    signature: "0x8f3d4a2b7c1e9d6f5a8c3b2e1d4f7a9c6b5e8d1a3f6c9b2e5d8a1c4f7b0e3d6a9c2f5e8b1d4a7c0f3e6b9d2a5c8f1e4b7d0a3c6f9e2b5d8a1c4f7a7c2",
    explorerUrl: "https://etherscan.io",
    balance: 125000,
    updatedAt: new Date().toISOString(),
  },
  {
    id: "w2",
    chain: "Bitcoin",
    address: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    label: "Reserve Wallet",
    verified: true,
    signature: "H8k2m5n9p3r7s1t4v6w8x0y2z5a7b9c1d3e5f7g9h1i3j5k7m9n1o3p5q7r9s1t3u5v7w9x1y3z5a7b9c1d9d1f",
    explorerUrl: "https://blockchair.com",
    balance: 48000,
    updatedAt: new Date().toISOString(),
  },
  {
    id: "w3",
    chain: "Polygon",
    address: "0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b",
    label: "Program Funds",
    verified: false,
    balance: 32000,
    updatedAt: new Date().toISOString(),
  },
];

export const seedRequests: SpendRequest[] = [
  {
    id: "r1",
    payee: "Downtown Property LLC",
    amount: 1500,
    category: "Housing",
    purpose: "Monthly rent for office space - December 2024",
    attachments: [],
    status: "Pending",
    requester: "Steward A",
    timeline: [
      { who: "Steward A", what: "Requested", when: new Date(Date.now() - 3600000).toISOString() },
    ],
    createdAt: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "r2",
    payee: "Community Outreach Initiative",
    amount: 450,
    category: "Program",
    purpose: "Educational materials and supplies for winter program",
    attachments: [],
    status: "Approved",
    requester: "Steward B",
    approver1: "Steward A",
    timeline: [
      { who: "Steward B", what: "Requested", when: new Date(Date.now() - 86400000).toISOString() },
      { who: "Steward A", what: "Approved", when: new Date(Date.now() - 43200000).toISOString() },
    ],
    createdAt: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: "r3",
    payee: "Tech Solutions Inc",
    amount: 12500,
    category: "Ops",
    purpose:
      "Annual software licenses and infrastructure upgrade for trust management systems",
    sourceHint: "Reserve Wallet",
    attachments: [],
    status: "Pending",
    requester: "Steward A",
    approver1: "Steward B",
    timeline: [
      { who: "Steward A", what: "Requested", when: new Date(Date.now() - 172800000).toISOString() },
      { who: "Steward B", what: "Approved", when: new Date(Date.now() - 86400000).toISOString() },
    ],
    createdAt: new Date(Date.now() - 172800000).toISOString(),
  },
];

export const seedLedger: LedgerEntry[] = [
  {
    id: "l1",
    dateISO: new Date(Date.now() - 2592000000).toISOString(),
    kind: "INFLOW",
    amount: 50000,
    category: "Grant",
    payee: "Foundation Donor",
    notes: "Q4 operational grant",
  },
  {
    id: "l2",
    dateISO: new Date(Date.now() - 1728000000).toISOString(),
    kind: "DISBURSE",
    amount: 1500,
    category: "Housing",
    payee: "Downtown Property LLC",
    ref: "r-prev-1",
    tx: "ACH-2024-11-001",
    notes: "November rent payment",
  },
  {
    id: "l3",
    dateISO: new Date(Date.now() - 864000000).toISOString(),
    kind: "DISBURSE",
    amount: 850,
    category: "Program",
    payee: "Local Food Bank",
    tx: "CHECK-2024-11-015",
    notes: "Monthly food program support",
  },
  {
    id: "l4",
    dateISO: new Date(Date.now() - 432000000).toISOString(),
    kind: "INFLOW",
    amount: 15000,
    category: "Donation",
    payee: "Anonymous Donor",
    tx: "0x7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b",
    notes: "Cryptocurrency donation - converted to USD",
  },
];

export const seedPolicy: Policy = {
  id: "policy1",
  selfApproveMax: 500,
  dualApproveMin: 500,
  governanceMin: 10000,
  cashWithdrawalCap: 200,
};

export const seedSnapshot: Snapshot = {
  id: "today",
  treasuryUSD: 125000,
  reserveUSD: 48000,
  programUSD: 32000,
  deltaUSD: 2500,
};
