const randomId = () => Math.random().toString(36).slice(2, 10);

const now = new Date();
const hoursAgo = (h) => new Date(now.getTime() - h * 60 * 60 * 1000).toISOString();

const mockUsers = {
  employee: {
    id: 'u-emp-1',
    full_name: 'Employee User',
    email: 'employee@gmail.com',
    role: 'employee',
    company_id: 'c-1',
  },
  it_staff: {
    id: 'u-staff-1',
    full_name: 'Raja',
    email: 'raja@gmail.com',
    role: 'it_staff',
    company_id: 'c-1',
  },
  company_admin: {
    id: 'u-admin-1',
    full_name: 'Company Admin',
    email: 'cpadmin@gmail.com',
    role: 'company_admin',
    company_id: 'c-1',
  },
  super_admin: {
    id: 'u-super-1',
    full_name: 'Sam Superadmin',
    email: 'superadmin@demo.com',
    role: 'super_admin',
    company_id: 'c-0',
  },
};

const pickUserByEmail = (email = '') => {
  const key = Object.keys(mockUsers).find((k) => mockUsers[k].email === email.toLowerCase());
  return key ? mockUsers[key] : mockUsers.employee;
};

let tickets = [
  {
    id: 't-1',
    ticket_number: 'HD-1001',
    title: 'VPN not connecting',
    description: 'Cannot connect to corporate VPN from home network.',
    status: 'new',
    priority: 'high',
    category: 'Network',
    source: 'web',
    created_at: hoursAgo(3),
    updated_at: hoursAgo(2),
    created_by_name: 'Alex Employee',
    assigned_to_name: 'Taylor IT',
    assigned_team: 'Network Ops',
    department: 'IT Support',
    ai_suggestion: 'Check VPN credentials and restart VPN client.',
    ai_confidence: 0.89,
    ai_predicted_category: 'Network',
  },
  {
    id: 't-2',
    ticket_number: 'HD-1002',
    title: 'Laptop camera driver issue',
    description: 'Camera not detected in Teams after update.',
    status: 'in_progress',
    priority: 'medium',
    category: 'Hardware',
    source: 'web',
    created_at: hoursAgo(10),
    updated_at: hoursAgo(1),
    created_by_name: 'Alex Employee',
    assigned_to_name: 'Taylor IT',
    assigned_team: 'Endpoint',
    department: 'IT Support',
    ai_suggestion: 'Reinstall webcam driver and reboot device.',
    ai_confidence: 0.76,
    ai_predicted_category: 'Hardware',
  },
  {
    id: 't-3',
    ticket_number: 'HD-1003',
    title: 'Password reset request',
    description: 'Forgot my SSO password and locked out.',
    status: 'resolved',
    priority: 'low',
    category: 'Access',
    source: 'chat',
    created_at: hoursAgo(28),
    updated_at: hoursAgo(26),
    created_by_name: 'Alex Employee',
    department: 'IT Support',
    ai_suggestion: 'Use self-service password reset portal.',
    ai_confidence: 0.94,
    ai_predicted_category: 'Access',
  },
];

const ticketMessages = {
  't-1': [
    { id: 'm-1', author_type: 'user', author_name: 'Alex Employee', content: 'VPN disconnected during meeting.', created_at: hoursAgo(3) },
    { id: 'm-2', author_type: 'ai', author_name: 'HelpDesk AI', content: 'Please verify your VPN profile and MFA approval.', created_at: hoursAgo(2.8) },
  ],
  't-2': [
    { id: 'm-3', author_type: 'user', author_name: 'Alex Employee', content: 'Camera is black in all apps.', created_at: hoursAgo(10) },
  ],
  't-3': [
    { id: 'm-4', author_type: 'ai', author_name: 'HelpDesk AI', content: 'Your password reset request was completed.', created_at: hoursAgo(26) },
  ],
};

let articles = [
  {
    id: 'a-1',
    title: 'How to troubleshoot VPN connectivity',
    content: 'Step-by-step VPN troubleshooting guide for remote users.',
    category: 'Network',
    author_name: 'Taylor IT',
    view_count: 154,
    updated_at: hoursAgo(20),
    created_at: hoursAgo(120),
  },
  {
    id: 'a-2',
    title: 'Reset your SSO password',
    content: 'Use the self-service flow at password.company.com.',
    category: 'Access',
    author_name: 'Jordan Admin',
    view_count: 89,
    updated_at: hoursAgo(45),
    created_at: hoursAgo(200),
  },
  {
    id: 'a-3',
    title: 'Fix common webcam issues',
    content: 'Driver refresh, privacy settings, and app permission checks.',
    category: 'Hardware',
    author_name: 'Taylor IT',
    view_count: 63,
    updated_at: hoursAgo(5),
    created_at: hoursAgo(70),
  },
];

let agents = [
  { id: 'ag-1', full_name: 'Taylor IT', email: 'itstaff@demo.com', role: 'it_staff', department: 'IT Support', status: 'online' },
  { id: 'ag-2', full_name: 'Casey Support', email: 'casey@demo.com', role: 'it_staff', department: 'IT Support', status: 'away' },
];

let teams = [
  { id: 'tm-1', name: 'Network Ops', description: 'Network incidents', email: 'network@demo.com', agent_ids: ['ag-1'] },
  { id: 'tm-2', name: 'Endpoint', description: 'Laptop and device support', email: 'endpoint@demo.com', agent_ids: ['ag-2'] },
];

let companies = [
  { id: 'c-1', name: 'Acme Corp', slug: 'acme', is_active: true, user_count: 42, ticket_count: 118, created_at: hoursAgo(1000) },
  { id: 'c-2', name: 'Globex', slug: 'globex', is_active: true, user_count: 19, ticket_count: 54, created_at: hoursAgo(2000) },
];

const mockResponse = (data, status = 200) => Promise.resolve({ data, status });

const parsePagination = (params = {}, defaultLimit = 10) => {
  const page = Number(params.page || 1);
  const limit = Number(params.limit || defaultLimit);
  return { page, limit, start: (page - 1) * limit, end: page * limit };
};

export const mockLogin = (email) => {
  const user = pickUserByEmail(email);
  return mockResponse({ access_token: 'mock-access-token', user });
};

export const mockGetMe = () => {
  const stored = localStorage.getItem('user');
  if (stored) {
    try {
      return mockResponse(JSON.parse(stored));
    } catch {
      return mockResponse(mockUsers.employee);
    }
  }
  return mockResponse(mockUsers.employee);
};

export const mockListTickets = (params = {}) => {
  let filtered = [...tickets];
  if (params.status) filtered = filtered.filter((t) => t.status === params.status);
  if (params.priority) filtered = filtered.filter((t) => t.priority === params.priority);
  if (params.category) filtered = filtered.filter((t) => t.category === params.category);
  if (params.search) {
    const q = String(params.search).toLowerCase();
    filtered = filtered.filter((t) => t.title.toLowerCase().includes(q) || t.description?.toLowerCase().includes(q) || t.ticket_number.toLowerCase().includes(q));
  }

  const { start, end } = parsePagination(params, 10);
  return mockResponse({ tickets: filtered.slice(start, end), total: filtered.length });
};

export const mockGetTicket = (id) => {
  const ticket = tickets.find((t) => t.id === id) || tickets[0];
  return mockResponse({ ...ticket, messages: ticketMessages[ticket.id] || [] });
};

export const mockCreateTicket = (data) => {
  const newTicket = {
    id: `t-${randomId()}`,
    ticket_number: `HD-${1000 + tickets.length + 1}`,
    title: data.title,
    description: data.description || '',
    status: 'new',
    priority: data.priority || 'medium',
    category: data.category || data.department || 'General',
    source: 'web',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    created_by_name: 'Alex Employee',
    department: data.department || 'IT Support',
    ai_suggestion: 'Thanks, your issue has been triaged and routed.',
    ai_confidence: 0.82,
    ai_predicted_category: data.category || 'General',
  };
  tickets = [newTicket, ...tickets];
  ticketMessages[newTicket.id] = [
    { id: `m-${randomId()}`, author_type: 'ai', author_name: 'HelpDesk AI', content: newTicket.ai_suggestion, created_at: new Date().toISOString() },
  ];
  return mockResponse(newTicket, 201);
};

export const mockUpdateTicket = (id, data) => {
  tickets = tickets.map((t) => (t.id === id ? { ...t, ...data, updated_at: new Date().toISOString() } : t));
  return mockResponse(tickets.find((t) => t.id === id));
};

export const mockAssignTicket = (id, data) => {
  tickets = tickets.map((t) => (t.id === id ? { ...t, assigned_to: data.assigned_to, status: 'assigned', updated_at: new Date().toISOString() } : t));
  return mockResponse({ success: true });
};

export const mockResolveTicket = (id) => {
  tickets = tickets.map((t) => (t.id === id ? { ...t, status: 'resolved', updated_at: new Date().toISOString() } : t));
  return mockResponse({ success: true });
};

export const mockGetMessages = (id) => mockResponse(ticketMessages[id] || []);

export const mockAddMessage = (id, data) => {
  const message = { id: `m-${randomId()}`, author_type: 'agent', author_name: 'Support Agent', content: data.content, created_at: new Date().toISOString() };
  ticketMessages[id] = [...(ticketMessages[id] || []), message];
  return mockResponse(message, 201);
};

export const mockGetSimilarArticles = () =>
  mockResponse(articles.slice(0, 3).map((a, i) => ({
    id: a.id,
    title: a.title,
    tag: a.category,
    summary: a.content,
    similarity: Number((0.93 - i * 0.1).toFixed(2)),
  })));

export const mockGetAiSuggestion = (id) => {
  const ticket = tickets.find((t) => t.id === id);
  return mockResponse({ text: ticket?.ai_suggestion || 'Restart affected service and validate access.', confidence: ticket?.ai_confidence ?? 0.74 });
};

export const mockGetOverview = () => {
  const active = tickets.filter((t) => !['resolved', 'closed'].includes(t.status)).length;
  return mockResponse({
    active_tickets: active,
    total_tickets_7d: tickets.length,
    avg_resolution_time: 6,
    sla_compliance: 94,
    ai_resolution_rate: 37,
  });
};

export const mockGetVolume = (period = '7d') => {
  const labels = period === '30d'
    ? ['W1', 'W2', 'W3', 'W4']
    : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const values = period === '30d' ? [42, 55, 38, 61] : [6, 9, 5, 11, 8, 4, 7];
  return mockResponse({ labels, values });
};

export const mockGetCategories = () => {
  const counts = tickets.reduce((acc, t) => {
    const key = t.category || 'General';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
  const categoriesData = Object.entries(counts).map(([category, count]) => ({ category, label: category, count }));
  const total = categoriesData.reduce((sum, c) => sum + c.count, 0);
  return mockResponse({ total, categories: categoriesData });
};

export const mockGetTeamPerformance = () => mockResponse([
  { team: 'Network Ops', resolved: 24, avg_hours: 5.1 },
  { team: 'Endpoint', resolved: 18, avg_hours: 6.4 },
]);

export const mockGetTrends = () => mockResponse({ items: [{ title: 'VPN incidents increased by 12%' }, { title: 'Password reset requests stable' }] });

export const mockListAgents = (params = {}) => {
  const { start, end } = parsePagination(params, 50);
  return mockResponse({ agents: agents.slice(start, end), total: agents.length });
};

export const mockCreateAgent = (data) => {
  const agent = { id: `ag-${randomId()}`, status: 'online', ...data };
  agents = [agent, ...agents];
  return mockResponse(agent, 201);
};

export const mockUpdateAgent = (id, data) => {
  agents = agents.map((a) => (a.id === id ? { ...a, ...data } : a));
  return mockResponse(agents.find((a) => a.id === id));
};

export const mockDeleteAgent = (id) => {
  agents = agents.filter((a) => a.id !== id);
  teams = teams.map((t) => ({ ...t, agent_ids: (t.agent_ids || []).filter((aid) => aid !== id) }));
  return mockResponse({ success: true });
};

export const mockListTeams = () => {
  const enriched = teams.map((t) => ({
    ...t,
    members: (t.agent_ids || []).map((aid) => agents.find((a) => a.id === aid)).filter(Boolean),
  }));
  return mockResponse(enriched);
};

export const mockCreateTeam = (data) => {
  const team = { id: `tm-${randomId()}`, ...data, agent_ids: [] };
  teams = [team, ...teams];
  return mockResponse(team, 201);
};

export const mockUpdateTeam = (id, data) => {
  teams = teams.map((t) => (t.id === id ? { ...t, ...data } : t));
  return mockResponse(teams.find((t) => t.id === id));
};

export const mockDeleteTeam = (id) => {
  teams = teams.filter((t) => t.id !== id);
  return mockResponse({ success: true });
};

export const mockAssignAgentToTeam = (teamId, agentId) => {
  teams = teams.map((t) => {
    if (t.id !== teamId) return t;
    const ids = new Set([...(t.agent_ids || []), agentId]);
    return { ...t, agent_ids: [...ids] };
  });
  return mockResponse({ success: true });
};

export const mockRemoveAgentFromTeam = (teamId, agentId) => {
  teams = teams.map((t) => (t.id === teamId ? { ...t, agent_ids: (t.agent_ids || []).filter((id) => id !== agentId) } : t));
  return mockResponse({ success: true });
};

export const mockGetMappings = () => mockResponse([
  { id: `map-${randomId()}`, company_id: 'c-1', category: 'Others', team_name: 'Others' },
]);
export const mockSaveMappings = (mappings) => mockResponse(mappings);
export const mockGetNotifications = () => mockResponse({ email_enabled: true, slack_enabled: false });
export const mockUpdateNotifications = (data) => mockResponse(data);

export const mockSendChat = (data) => {
  const message = String(data.message || '').toLowerCase();
  const ticketCreated = message.includes('ticket') || message.includes('issue') || message.includes('problem');
  return mockResponse({
    response: ticketCreated
      ? 'I can help with that. I created a draft support ticket and routed it to IT Support.'
      : 'I can help troubleshoot that. Please share any error text you see.',
    ticket_created: ticketCreated,
  });
};

export const mockListArticles = (params = {}) => {
  let filtered = [...articles];
  if (params.search) {
    const q = String(params.search).toLowerCase();
    filtered = filtered.filter((a) => a.title.toLowerCase().includes(q) || a.content.toLowerCase().includes(q));
  }
  if (params.category) filtered = filtered.filter((a) => a.category === params.category);

  const { start, end } = parsePagination(params, 12);
  return mockResponse({ articles: filtered.slice(start, end), total: filtered.length });
};

export const mockGetArticle = (id) => {
  const article = articles.find((a) => a.id === id);
  return mockResponse(article || null);
};

export const mockCreateArticle = (data) => {
  const article = {
    id: `a-${randomId()}`,
    title: data.title,
    content: data.content,
    category: data.category || 'General',
    author_name: 'Taylor IT',
    view_count: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  articles = [article, ...articles];
  return mockResponse(article, 201);
};

export const mockUpdateArticle = (id, data) => {
  articles = articles.map((a) => (a.id === id ? { ...a, ...data, updated_at: new Date().toISOString() } : a));
  return mockResponse(articles.find((a) => a.id === id));
};

export const mockDeleteArticle = (id) => {
  articles = articles.filter((a) => a.id !== id);
  return mockResponse({ success: true });
};

export const mockGetStats = () => mockResponse({
  total_companies: companies.length,
  total_users: companies.reduce((sum, c) => sum + (c.user_count || 0), 0),
  active_tickets: tickets.filter((t) => !['resolved', 'closed'].includes(t.status)).length,
  ai_resolution_rate: 0.39,
  total_articles: articles.length,
  avg_response_time: '< 2s',
  ai_queries_daily: 128,
});

export const mockListCompanies = () => mockResponse({ companies });

export const mockCreateCompany = (data) => {
  const company = {
    id: `c-${randomId()}`,
    name: data.name,
    slug: data.slug,
    is_active: true,
    user_count: 1,
    ticket_count: 0,
    created_at: new Date().toISOString(),
  };
  companies = [company, ...companies];
  return mockResponse(company, 201);
};

export const mockUpdateCompany = (id, data) => {
  companies = companies.map((c) => (c.id === id ? { ...c, ...data } : c));
  return mockResponse(companies.find((c) => c.id === id));
};

export const mockDeleteCompany = (id) => {
  companies = companies.filter((c) => c.id !== id);
  return mockResponse({ success: true });
};
