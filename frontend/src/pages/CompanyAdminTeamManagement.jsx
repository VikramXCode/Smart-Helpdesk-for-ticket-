import { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { AdminLayout } from '../components/AdminLayout';
import {
  assignAgentToTeam,
  createAgent,
  createTeam,
  deleteTeam,
  listAgents,
  listTeams,
  removeAgentFromTeam,
  updateTeam,
} from '../api/admin';

const emptyTeamForm = { name: '', description: '' };
const emptyAgentForm = { full_name: '', email: '', team_id: '' };

const CompanyAdminTeamManagement = () => {
  const [teams, setTeams] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showTeamModal, setShowTeamModal] = useState(false);
  const [teamForm, setTeamForm] = useState(emptyTeamForm);
  const [editingTeamId, setEditingTeamId] = useState(null);
  const [savingTeam, setSavingTeam] = useState(false);

  const [showAgentModal, setShowAgentModal] = useState(false);
  const [agentForm, setAgentForm] = useState(emptyAgentForm);
  const [savingAgent, setSavingAgent] = useState(false);

  const loadData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [teamRes, agentRes] = await Promise.all([
        listTeams(),
        listAgents({ limit: 100 }),
      ]);
      setTeams(teamRes.data || []);
      setAgents(agentRes.data?.agents || []);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load team management data');
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openCreateTeam = () => {
    setEditingTeamId(null);
    setTeamForm(emptyTeamForm);
    setShowTeamModal(true);
  };

  const openEditTeam = (team) => {
    setEditingTeamId(team.id);
    setTeamForm({ name: team.name || '', description: team.description || '' });
    setShowTeamModal(true);
  };

  const handleSaveTeam = async (e) => {
    e.preventDefault();

    if ((teamForm.name || '').trim().length < 2) {
      toast.error('Team name must be at least 2 characters');
      return;
    }
    if ((teamForm.description || '').trim().length < 10) {
      toast.error('Please enter a detailed description (at least 10 characters)');
      return;
    }

    setSavingTeam(true);
    try {
      const payload = {
        name: teamForm.name.trim(),
        description: teamForm.description.trim(),
      };

      if (editingTeamId) {
        await updateTeam(editingTeamId, payload);
        toast.success('Team updated');
      } else {
        await createTeam(payload);
        toast.success('Team created');
      }

      setShowTeamModal(false);
      setTeamForm(emptyTeamForm);
      setEditingTeamId(null);
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save team');
    } finally {
      setSavingTeam(false);
    }
  };

  const handleDeleteTeam = async (teamId, teamName) => {
    if (!window.confirm(`Delete team "${teamName}"?`)) return;
    try {
      await deleteTeam(teamId);
      toast.success('Team deleted');
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete team');
    }
  };

  const handleCreateAgent = async (e) => {
    e.preventDefault();

    if (!teams.length) {
      toast.error('Create a team first before adding agents');
      return;
    }

    if (!agentForm.team_id) {
      toast.error('Select a team for this agent');
      return;
    }

    setSavingAgent(true);
    try {
      await createAgent({
        full_name: agentForm.full_name.trim(),
        email: agentForm.email.trim(),
        role: 'it_staff',
        team_id: agentForm.team_id,
      });

      toast.success('Agent created and assigned to team');
      setAgentForm(emptyAgentForm);
      setShowAgentModal(false);
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create agent');
    } finally {
      setSavingAgent(false);
    }
  };

  const handleTeamReassign = async (agent, teamId) => {
    const previousTeamId = agent.team_id || null;
    const nextTeamId = teamId || null;

    if (previousTeamId === nextTeamId) return;

    try {
      if (!teamId) {
        if (agent.team_id) {
          await removeAgentFromTeam(agent.team_id, agent.id);
        }
      } else {
        await assignAgentToTeam(teamId, agent.id);
      }

      setAgents((prev) =>
        prev.map((row) => {
          if (row.id !== agent.id) return row;
          const matchedTeam = teams.find((team) => team.id === nextTeamId);
          return {
            ...row,
            team_id: nextTeamId,
            team_name: matchedTeam?.name || null,
          };
        })
      );

      setTeams((prev) =>
        prev.map((team) => {
          let memberCount = team.member_count || 0;
          if (previousTeamId && team.id === previousTeamId) memberCount = Math.max(0, memberCount - 1);
          if (nextTeamId && team.id === nextTeamId) memberCount += 1;
          return memberCount === (team.member_count || 0) ? team : { ...team, member_count: memberCount };
        })
      );

      toast.success('Agent team updated');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update agent team');
    }
  };

  const teamsById = useMemo(() => {
    const map = {};
    teams.forEach((team) => {
      map[team.id] = team;
    });
    return map;
  }, [teams]);

  const headerAction = (
    <div className="flex items-center gap-2">
      <button
        onClick={() => {
          if (!teams.length) {
            toast.error('Create a team first before adding agents');
            return;
          }
          setAgentForm((prev) => ({ ...prev, team_id: prev.team_id || teams[0]?.id || '' }));
          setShowAgentModal(true);
        }}
        className="flex items-center gap-2 h-9 px-4 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
      >
        <span className="material-symbols-outlined text-[18px]">person_add</span>
        Add Agent
      </button>
      <button
        onClick={openCreateTeam}
        className="flex items-center gap-2 h-9 px-4 bg-primary text-white text-sm font-medium rounded-lg hover:bg-slate-800 transition-colors"
      >
        <span className="material-symbols-outlined text-[18px]">group_add</span>
        Add Team
      </button>
    </div>
  );

  return (
    <AdminLayout title="Team Management" headerAction={headerAction}>
      <div className="p-6 space-y-6">
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">How this works</h3>
          <p className="text-sm text-slate-500 mt-1">
            Team name acts as the category label. Create teams using only team name and detailed description, then add agents to those teams.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Teams</h3>
              <span className="text-xs text-slate-500">{teams.length} total</span>
            </div>

            {loading ? (
              <p className="text-sm text-slate-500">Loading teams...</p>
            ) : teams.length === 0 ? (
              <p className="text-sm text-slate-500">No teams created yet. Add a team first.</p>
            ) : (
              <div className="space-y-3">
                {teams.map((team) => (
                  <div key={team.id} className="rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-slate-900 dark:text-white">{team.name}</p>
                        <p className="text-xs text-slate-500 mt-1 whitespace-pre-wrap">{team.description || 'No description'}</p>
                        <p className="text-[11px] text-slate-400 mt-2">Members: {team.member_count || 0}</p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button onClick={() => openEditTeam(team)} className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600">
                          <span className="material-symbols-outlined text-[18px]">edit</span>
                        </button>
                        <button onClick={() => handleDeleteTeam(team.id, team.name)} className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600">
                          <span className="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Agents</h3>
              <span className="text-xs text-slate-500">{agents.length} total</span>
            </div>

            {loading ? (
              <p className="text-sm text-slate-500">Loading agents...</p>
            ) : !teams.length ? (
              <p className="text-sm text-slate-500">Create at least one team before managing agents.</p>
            ) : agents.length === 0 ? (
              <p className="text-sm text-slate-500">No agents yet. Click Add Agent to create one.</p>
            ) : (
              <div className="space-y-3">
                {agents.map((agent) => (
                  <div key={agent.id} className="rounded-lg border border-slate-200 dark:border-slate-700 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-slate-900 dark:text-white">{agent.name}</p>
                        <p className="text-xs text-slate-500">{agent.email}</p>
                      </div>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                        {agent.status || 'offline'}
                      </span>
                    </div>

                    <div className="mt-3">
                      <label className="text-xs text-slate-500">Assigned Team</label>
                      <select
                        className="mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-3 py-2"
                        value={agent.team_id || ''}
                        onChange={(e) => handleTeamReassign(agent, e.target.value)}
                      >
                        <option value="">Unassigned</option>
                        {teams.map((team) => (
                          <option key={team.id} value={team.id}>{team.name}</option>
                        ))}
                      </select>
                      {agent.team_id && teamsById[agent.team_id] && (
                        <p className="text-[11px] text-slate-400 mt-1">Current: {teamsById[agent.team_id].name}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {showTeamModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowTeamModal(false)}>
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-lg w-full p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
              {editingTeamId ? 'Edit Team' : 'Create Team'}
            </h3>
            <form onSubmit={handleSaveTeam} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 block">Team Name</label>
                <input
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5"
                  placeholder="e.g. Network"
                  value={teamForm.name}
                  onChange={(e) => setTeamForm((prev) => ({ ...prev, name: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 block">Detailed Description</label>
                <textarea
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5"
                  placeholder="Describe in detail what this team handles"
                  rows={4}
                  value={teamForm.description}
                  onChange={(e) => setTeamForm((prev) => ({ ...prev, description: e.target.value }))}
                  required
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowTeamModal(false)} className="flex-1 px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50">
                  Cancel
                </button>
                <button type="submit" disabled={savingTeam} className="flex-1 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-60">
                  {savingTeam ? 'Saving...' : editingTeamId ? 'Update Team' : 'Create Team'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showAgentModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowAgentModal(false)}>
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-md w-full p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Add Agent</h3>
            <form onSubmit={handleCreateAgent} className="space-y-4">
              <input
                className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5"
                placeholder="Full Name"
                value={agentForm.full_name}
                onChange={(e) => setAgentForm((prev) => ({ ...prev, full_name: e.target.value }))}
                required
              />
              <input
                className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5"
                type="email"
                placeholder="Email"
                value={agentForm.email}
                onChange={(e) => setAgentForm((prev) => ({ ...prev, email: e.target.value }))}
                required
              />
              <div className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-sm px-4 py-2.5 text-slate-500 dark:text-slate-300">
                Default password: 12345678 (agent must change on first login)
              </div>
              <select
                className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-sm px-4 py-2.5"
                value={agentForm.team_id}
                onChange={(e) => setAgentForm((prev) => ({ ...prev, team_id: e.target.value }))}
                required
              >
                <option value="">Select Team</option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>{team.name}</option>
                ))}
              </select>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowAgentModal(false)} className="flex-1 px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50">
                  Cancel
                </button>
                <button type="submit" disabled={savingAgent} className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-60">
                  {savingAgent ? 'Adding...' : 'Add Agent'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};

export default CompanyAdminTeamManagement;
