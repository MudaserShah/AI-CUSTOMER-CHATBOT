import React, { useEffect, useState } from "react";
import {
  API_BASE_URL,
  type Project,
  type DocumentItem,
  type ProjectTool,
  listProjects,
  createProject,
  updateProject,
  listProjectDocs,
  uploadProjectDocs,
  deleteProjectDoc,
  listProjectTools,
  createProjectTool,
  deleteProjectTool,
} from "./api";

export default function ProjectManager() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("technest-default");
  const [loading, setLoading] = useState(true);
  const [saveLoading, setSaveLoading] = useState(false);
  const [msg, setMsg] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // Active project form state
  const [name, setName] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [widgetTitle, setWidgetTitle] = useState("");
  const [widgetGreeting, setWidgetGreeting] = useState("");
  const [primaryColor, setPrimaryColor] = useState("#2563eb");
  const [apiKey, setApiKey] = useState("");

  // RAG documents state
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Dynamic Tools state
  const [tools, setTools] = useState<ProjectTool[]>([]);
  const [toolName, setToolName] = useState("");
  const [toolDesc, setToolDesc] = useState("");
  const [toolMethod, setToolMethod] = useState("GET");
  const [toolUrl, setToolUrl] = useState("");
  const [showToolModal, setShowToolModal] = useState(false);

  // Create Project Modal state
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");

  const activeProject = projects.find((p) => p.id === selectedProjectId) || projects[0];

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (activeProject) {
      setName(activeProject.name || "");
      setSystemPrompt(activeProject.system_prompt || "");
      setWidgetTitle(activeProject.widget_title || "");
      setWidgetGreeting(activeProject.widget_greeting || "");
      setPrimaryColor(activeProject.primary_color || "#2563eb");
      setApiKey(activeProject.api_key || "");

      loadProjectDocs(activeProject.id);
      loadTools(activeProject.id);
    }
  }, [selectedProjectId, projects]);

  async function loadProjects() {
    try {
      setLoading(true);
      const data = await listProjects();
      setProjects(data);
      if (data.length > 0 && !data.some((p) => p.id === selectedProjectId)) {
        setSelectedProjectId(data[0].id);
      }
    } catch (err) {
      setMsg({ text: "Failed to load projects", type: "error" });
    } finally {
      setLoading(false);
    }
  }

  async function loadProjectDocs(pId: string) {
    try {
      setDocsLoading(true);
      const items = await listProjectDocs(pId);
      setDocs(items);
    } catch {
      setDocs([]);
    } finally {
      setDocsLoading(false);
    }
  }

  async function loadTools(pId: string) {
    try {
      const list = await listProjectTools(pId);
      setTools(list);
    } catch {
      setTools([]);
    }
  }

  async function handleSaveConfig(e: React.FormEvent) {
    e.preventDefault();
    if (!activeProject) return;
    try {
      setSaveLoading(true);
      const updated = await updateProject(activeProject.id, {
        name,
        system_prompt: systemPrompt,
        widget_title: widgetTitle,
        widget_greeting: widgetGreeting,
        primary_color: primaryColor,
      });
      setProjects((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      setMsg({ text: "Bot settings updated successfully!", type: "success" });
    } catch (err: any) {
      setMsg({ text: err.message || "Failed to update project", type: "error" });
    } finally {
      setSaveLoading(false);
      setTimeout(() => setMsg(null), 4000);
    }
  }

  async function handleCreateProject(e: React.FormEvent) {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      const created = await createProject({
        name: newProjectName.trim(),
        widget_title: `${newProjectName.trim()} Assistant`,
        widget_greeting: `Hello! Welcome to ${newProjectName.trim()}. How can I help you today?`,
        primary_color: "#2563eb",
      });
      setProjects((prev) => [...prev, created]);
      setSelectedProjectId(created.id);
      setShowNewProjectModal(false);
      setNewProjectName("");
      setMsg({ text: `Project "${created.name}" created!`, type: "success" });
    } catch (err: any) {
      setMsg({ text: err.message || "Could not create project", type: "error" });
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    if (!e.target.files || e.target.files.length === 0 || !activeProject) return;
    try {
      setUploading(true);
      await uploadProjectDocs(activeProject.id, e.target.files);
      setMsg({ text: "Knowledge document indexed successfully!", type: "success" });
      loadProjectDocs(activeProject.id);
    } catch (err: any) {
      setMsg({ text: err.message || "Upload failed", type: "error" });
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleDeleteDoc(docId: string) {
    if (!activeProject) return;
    try {
      await deleteProjectDoc(activeProject.id, docId);
      setDocs((prev) => prev.filter((d) => d.doc_id !== docId));
      setMsg({ text: "Document removed", type: "success" });
    } catch {
      setMsg({ text: "Failed to delete document", type: "error" });
    }
  }

  async function handleCreateTool(e: React.FormEvent) {
    e.preventDefault();
    if (!activeProject || !toolName || !toolUrl) return;
    try {
      const newTool = await createProjectTool(activeProject.id, {
        name: toolName.trim(),
        description: toolDesc.trim(),
        method: toolMethod,
        endpoint_url: toolUrl.trim(),
      });
      setTools((prev) => [...prev, newTool]);
      setShowToolModal(false);
      setToolName("");
      setToolDesc("");
      setToolUrl("");
      setMsg({ text: `Tool "${newTool.name}" created!`, type: "success" });
    } catch (err: any) {
      setMsg({ text: err.message || "Failed to create tool", type: "error" });
    }
  }

  async function handleDeleteTool(toolId: string) {
    try {
      await deleteProjectTool(activeProject.id, toolId);
      setTools((prev) => prev.filter((t) => t.id !== toolId));
    } catch {}
  }

  const embedScriptSnippet = `<!-- AI Chatbot Embed Code (Paste before </body>) -->\n<script\n  src="${API_BASE_URL}/static/widget.js"\n  data-project-id="${activeProject?.id || "technest-default"}"\n  data-api-url="${API_BASE_URL}"\n  defer>\n</script>`;

  if (loading) {
    return <div style={{ padding: "40px", textAlign: "center" }}>Loading SaaS Projects...</div>;
  }

  return (
    <div style={{ maxWidth: "1100px", margin: "30px auto", padding: "0 20px" }}>
      {/* Top Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: "700", color: "#0f172a" }}>AI Chatbot SaaS Dashboard</h1>
          <p style={{ color: "#64748b", fontSize: "14px", marginTop: "4px" }}>
            Manage multiple client projects, customize AI personas, upload RAG knowledge, and copy embed codes.
          </p>
        </div>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            style={{
              padding: "10px 14px",
              borderRadius: "8px",
              border: "1px solid #cbd5e1",
              fontSize: "14px",
              fontWeight: "600",
              background: "#ffffff",
              cursor: "pointer",
            }}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.id === "technest-default" ? "Default Store" : p.slug})
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => setShowNewProjectModal(true)}
            style={{
              padding: "10px 18px",
              borderRadius: "8px",
              background: "#2563eb",
              color: "#ffffff",
              border: "none",
              fontWeight: "600",
              cursor: "pointer",
            }}
          >
            + New Project
          </button>
        </div>
      </div>

      {msg && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "8px",
            marginBottom: "20px",
            background: msg.type === "success" ? "#dcfce7" : "#fee2e2",
            color: msg.type === "success" ? "#166534" : "#991b1b",
            fontSize: "14px",
            fontWeight: "500",
          }}
        >
          {msg.text}
        </div>
      )}

      {/* Main Grid: Settings & Embed on Left, Knowledge & Tools on Right */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "24px" }}>
        {/* Left Column: Bot Settings Form */}
        <div>
          <div style={{ background: "#ffffff", padding: "24px", borderRadius: "16px", border: "1px solid #e2e8f0", marginBottom: "24px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "600", marginBottom: "16px", color: "#0f172a" }}>
              Bot Persona & Appearance
            </h2>
            <form onSubmit={handleSaveConfig} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", color: "#334155", marginBottom: "6px" }}>
                  Project Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", fontSize: "14px" }}
                  required
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", color: "#334155", marginBottom: "6px" }}>
                  Project API Key (Public Client Key)
                </label>
                <div style={{ display: "flex", gap: "8px" }}>
                  <input
                    type="text"
                    value={apiKey}
                    readOnly
                    style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", fontSize: "13px", background: "#f8fafc", fontFamily: "monospace" }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(apiKey);
                      setMsg({ text: "API Key copied to clipboard!", type: "success" });
                    }}
                    style={{ padding: "8px 14px", borderRadius: "8px", background: "#f1f5f9", border: "1px solid #cbd5e1", cursor: "pointer", fontSize: "12px", whiteSpace: "nowrap" }}
                  >
                    Copy Key
                  </button>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", color: "#334155", marginBottom: "6px" }}>
                  Widget Header Title
                </label>
                <input
                  type="text"
                  value={widgetTitle}
                  onChange={(e) => setWidgetTitle(e.target.value)}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", fontSize: "14px" }}
                  required
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", color: "#334155", marginBottom: "6px" }}>
                  Greeting Message
                </label>
                <textarea
                  value={widgetGreeting}
                  onChange={(e) => setWidgetGreeting(e.target.value)}
                  rows={2}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", fontSize: "14px" }}
                  required
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", color: "#334155", marginBottom: "6px" }}>
                  Primary Brand Color
                </label>
                <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                  <input
                    type="color"
                    value={primaryColor}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    style={{ width: "42px", height: "42px", borderRadius: "8px", border: "1px solid #cbd5e1", cursor: "pointer" }}
                  />
                  <input
                    type="text"
                    value={primaryColor}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    style={{ width: "120px", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", fontSize: "14px" }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", color: "#334155", marginBottom: "6px" }}>
                  Custom System Prompt (Agent Persona & Rules)
                </label>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  rows={5}
                  placeholder="Leave blank to use default assistant prompt..."
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", fontSize: "13px", fontFamily: "monospace" }}
                />
              </div>

              <button
                type="submit"
                disabled={saveLoading}
                style={{
                  padding: "12px",
                  borderRadius: "8px",
                  background: primaryColor || "#2563eb",
                  color: "#ffffff",
                  border: "none",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                {saveLoading ? "Saving..." : "Save Bot Settings"}
              </button>
            </form>
          </div>

          {/* Embed Script Card */}
          <div style={{ background: "#0f172a", color: "#ffffff", padding: "24px", borderRadius: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: "600" }}>Embed On Any Website</h3>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(embedScriptSnippet);
                  setMsg({ text: "Embed script copied to clipboard!", type: "success" });
                }}
                style={{
                  background: "rgba(255,255,255,0.15)",
                  color: "#ffffff",
                  border: "none",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Copy Code
              </button>
            </div>
            <p style={{ color: "#94a3b8", fontSize: "13px", marginBottom: "12px" }}>
              Give this single script tag to your client. Works on Shopify, WordPress, Webflow, or custom React/HTML sites!
            </p>
            <pre style={{ background: "#020617", padding: "14px", borderRadius: "8px", overflowX: "auto", fontSize: "12px", color: "#38bdf8" }}>
              {embedScriptSnippet}
            </pre>
            <div style={{ marginTop: "14px" }}>
              <a
                href={`${API_BASE_URL}/static/demo_client.html`}
                target="_blank"
                rel="noreferrer"
                style={{ color: "#60a5fa", fontSize: "13px", textDecoration: "underline" }}
              >
                Open Live External Client Website Demo →
              </a>
            </div>
          </div>
        </div>

        {/* Right Column: Knowledge Base (RAG) & Dynamic Tools */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Project Knowledge Base */}
          <div style={{ background: "#ffffff", padding: "24px", borderRadius: "16px", border: "1px solid #e2e8f0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "18px", fontWeight: "600", color: "#0f172a" }}>Knowledge Base (RAG)</h2>
              <label
                style={{
                  background: "#f1f5f9",
                  padding: "6px 14px",
                  borderRadius: "8px",
                  fontSize: "13px",
                  fontWeight: "600",
                  cursor: "pointer",
                  color: "#334155",
                }}
              >
                {uploading ? "Indexing..." : "+ Upload File"}
                <input
                  type="file"
                  onChange={handleFileUpload}
                  multiple
                  accept=".pdf,.docx,.md,.csv,.txt"
                  style={{ display: "none" }}
                  disabled={uploading}
                />
              </label>
            </div>
            <p style={{ fontSize: "13px", color: "#64748b", marginBottom: "14px" }}>
              Documents are strictly scoped to project <strong>{activeProject?.name}</strong> in Qdrant Vector DB.
            </p>

            {docsLoading ? (
              <div style={{ fontSize: "13px", color: "#64748b" }}>Loading documents...</div>
            ) : docs.length === 0 ? (
              <div style={{ padding: "20px", textAlign: "center", background: "#f8fafc", borderRadius: "8px", color: "#94a3b8", fontSize: "13px" }}>
                No documents uploaded for this project yet.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "220px", overflowY: "auto" }}>
                {docs.map((d) => (
                  <div
                    key={d.doc_id}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "10px 12px",
                      background: "#f8fafc",
                      borderRadius: "8px",
                      border: "1px solid #f1f5f9",
                      fontSize: "13px",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: "600", color: "#0f172a" }}>{d.file_name}</div>
                      <div style={{ fontSize: "11px", color: "#64748b" }}>
                        {d.total_chunks} chunk(s) • {d.file_type.toUpperCase()}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteDoc(d.doc_id)}
                      style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: "12px" }}
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Dynamic Tools / Webhooks */}
          <div style={{ background: "#ffffff", padding: "24px", borderRadius: "16px", border: "1px solid #e2e8f0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "18px", fontWeight: "600", color: "#0f172a" }}>Agentic Tools & Webhooks</h2>
              <button
                type="button"
                onClick={() => setShowToolModal(true)}
                style={{
                  background: "#f1f5f9",
                  padding: "6px 14px",
                  borderRadius: "8px",
                  fontSize: "13px",
                  fontWeight: "600",
                  cursor: "pointer",
                  color: "#334155",
                  border: "none",
                }}
              >
                + Add Webhook Tool
              </button>
            </div>
            <p style={{ fontSize: "13px", color: "#64748b", marginBottom: "14px" }}>
              Connect custom REST endpoints (order lookup, booking, reservations) for the AI agent to call dynamically.
            </p>

            {tools.length === 0 ? (
              <div style={{ padding: "20px", textAlign: "center", background: "#f8fafc", borderRadius: "8px", color: "#94a3b8", fontSize: "13px" }}>
                {activeProject?.id === "technest-default"
                  ? "TechNest default tools (get_order, create_refund, change_delivery_address) are active."
                  : "No custom tools connected. The agent will use Knowledge Base RAG."}
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {tools.map((t) => (
                  <div
                    key={t.id}
                    style={{
                      padding: "10px 12px",
                      background: "#f8fafc",
                      borderRadius: "8px",
                      border: "1px solid #f1f5f9",
                      fontSize: "13px",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: "600", color: "#0f172a" }}>
                        <span style={{ background: "#e2e8f0", padding: "2px 6px", borderRadius: "4px", fontSize: "11px", marginRight: "6px" }}>
                          {t.method}
                        </span>
                        {t.name}
                      </div>
                      <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>{t.endpoint_url}</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteTool(t.id)}
                      style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: "12px" }}
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New Project Modal */}
      {showNewProjectModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
          }}
        >
          <div style={{ background: "#ffffff", padding: "28px", borderRadius: "16px", width: "420px", maxWidth: "90%" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "14px" }}>Create New SaaS Project</h3>
            <form onSubmit={handleCreateProject} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "6px" }}>Project Name</label>
                <input
                  type="text"
                  placeholder="e.g. Acme Clothing, Shoes Store, Agency Bot"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                  required
                />
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
                <button
                  type="button"
                  onClick={() => setShowNewProjectModal(false)}
                  style={{ padding: "8px 14px", borderRadius: "8px", background: "#f1f5f9", border: "none", cursor: "pointer" }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ padding: "8px 16px", borderRadius: "8px", background: "#2563eb", color: "#ffffff", border: "none", fontWeight: "600", cursor: "pointer" }}
                >
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Webhook Tool Modal */}
      {showToolModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
          }}
        >
          <div style={{ background: "#ffffff", padding: "28px", borderRadius: "16px", width: "480px", maxWidth: "90%" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "14px" }}>Add Dynamic Tool / Webhook</h3>
            <form onSubmit={handleCreateTool} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "6px" }}>Tool Identifier</label>
                <input
                  type="text"
                  placeholder="e.g. check_order, track_shipment"
                  value={toolName}
                  onChange={(e) => setToolName(e.target.value)}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                  required
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "6px" }}>Description for AI</label>
                <input
                  type="text"
                  placeholder="e.g. Check customer order status from Shopify API"
                  value={toolDesc}
                  onChange={(e) => setToolDesc(e.target.value)}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                  required
                />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "100px 1fr", gap: "10px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "6px" }}>Method</label>
                  <select
                    value={toolMethod}
                    onChange={(e) => setToolMethod(e.target.value)}
                    style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                  >
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "6px" }}>Endpoint URL</label>
                  <input
                    type="url"
                    placeholder="https://api.mystore.com/orders/{order_id}"
                    value={toolUrl}
                    onChange={(e) => setToolUrl(e.target.value)}
                    style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                    required
                  />
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
                <button
                  type="button"
                  onClick={() => setShowToolModal(false)}
                  style={{ padding: "8px 14px", borderRadius: "8px", background: "#f1f5f9", border: "none", cursor: "pointer" }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ padding: "8px 16px", borderRadius: "8px", background: "#2563eb", color: "#ffffff", border: "none", fontWeight: "600", cursor: "pointer" }}
                >
                  Add Tool
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
