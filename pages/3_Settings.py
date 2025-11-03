
import streamlit as st
import requests
from uuid import uuid4

# ======================================================================================
# GENERAL API AND CONFIGURATION
# ======================================================================================

st.set_page_config(page_title="Settings", layout="wide")
st.title("Settings")

def get_api_url():
    return "http://127.0.0.1:8001/api"

# ======================================================================================
# SESSION STATE INITIALIZATION
# ======================================================================================

# Initialize all session states at the beginning
if 'bert_settings' not in st.session_state:
    st.session_state.bert_settings = {}
if 'jira_settings' not in st.session_state:
    st.session_state.jira_settings = {}
if 'ollama_settings' not in st.session_state:
    st.session_state.ollama_settings = {}
if 'ollama_models' not in st.session_state:
    st.session_state.ollama_models = []
if 'llm_monitoring_settings' not in st.session_state:
    st.session_state.llm_monitoring_settings = {}
if 'jira_modules' not in st.session_state:
    st.session_state.jira_modules = []
if 'samba_settings' not in st.session_state:
    st.session_state.samba_settings = {}

# ======================================================================================
# TABS DEFINITION
# ======================================================================================

tab_jira_modules, tab_bert, tab_jira, tab_ollama, tab_llm, tab_samba, tab_system = st.tabs([
    "Jira Modules", "Bert", "Jira", "Ollama", "LLM Monitoring", "Samba", "System",
])

# ======================================================================================
# JIRA MODULES TAB
# ======================================================================================
with tab_jira_modules:
    st.header("Jira Modules")

    # --- Helper Functions for Jira Modules ---
    def fetch_jira_modules():
        try:
            response = requests.get(f"{get_api_url()}/settings/jira-modules")
            response.raise_for_status()
            modules = response.json()
            for module in modules:
                if 'client_id' not in module:
                    module['client_id'] = str(uuid4())
            st.session_state.jira_modules = modules
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch Jira modules: {e}")
            st.session_state.jira_modules = []

    def save_all_jira_modules(modules):
        modules_to_save = [{k: v for k, v in module.items() if k != 'client_id'} for module in modules]
        try:
            response = requests.post(f"{get_api_url()}/settings/jira-modules", json=modules_to_save)
            response.raise_for_status()
            st.success("All modules saved successfully!")
            return True
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to save modules: {e}")
            return False

    # --- Dialogs for Jira Modules ---
    @st.dialog("Module Details")
    def module_dialog(module_client_id=None):
        is_new = module_client_id is None
        module_data = next((m for m in st.session_state.jira_modules if m['client_id'] == module_client_id), None) if not is_new else {"name": "", "url": "", "isEnabled": True}

        with st.form("module_form"):
            name = st.text_input("Module Name", value=module_data.get("name", ""))
            url = st.text_input("URL", value=module_data.get("url", ""))
            is_enabled = st.toggle("Enabled", value=module_data.get("isEnabled", True))
            
            if st.form_submit_button("Save"):
                updated_module = {"name": name, "url": url, "isEnabled": is_enabled}
                if is_new:
                    updated_module['client_id'] = str(uuid4())
                    st.session_state.jira_modules.append(updated_module)
                else:
                    index = next((i for i, m in enumerate(st.session_state.jira_modules) if m['client_id'] == module_client_id), -1)
                    if index != -1:
                        st.session_state.jira_modules[index].update(updated_module)
                st.rerun()

    @st.dialog("Confirm Deletion")
    def delete_dialog(module_client_id):
        module_data = next((m for m in st.session_state.jira_modules if m['client_id'] == module_client_id), None)
        st.write(f"Are you sure you want to delete the module **'{module_data.get('name')}'**?")
        st.warning("This change is temporary. Click 'Save All Changes' to make it permanent.")
        
        if st.button("Yes, Delete", type="primary"):
            st.session_state.jira_modules = [m for m in st.session_state.jira_modules if m['client_id'] != module_client_id]
            st.rerun()

    # --- UI for Jira Modules ---
    if not st.session_state.jira_modules:
        fetch_jira_modules()

    if st.button("Add New Module", type="secondary"):
        module_dialog()

    st.divider()

    if not st.session_state.jira_modules:
        st.info("No Jira modules configured yet. Add one to get started.")
    else:
        for module in st.session_state.jira_modules:
            col1, col2, col3, col4 = st.columns([3, 5, 1, 1])
            with col1:
                st.write(f"**{module.get('name', 'No Name')}**")
                st.caption(f"Status: {'Enabled' if module.get('isEnabled') else 'Disabled'}")
            with col2:
                st.code(module.get('url', 'No URL'), language="")
            with col3:
                if st.button("Edit", key=f"edit_{module['client_id']}", use_container_width=True):
                    module_dialog(module['client_id'])
            with col4:
                if st.button("Delete", key=f"delete_{module['client_id']}", type="primary", use_container_width=True):
                    delete_dialog(module['client_id'])
    
    st.divider()
    if st.button("Save All Changes to Backend", type="primary"):
        if save_all_jira_modules(st.session_state.jira_modules):
            fetch_jira_modules()
            st.rerun()

# ======================================================================================
# BERT SETTINGS TAB
# ======================================================================================
with tab_bert:
    st.header("Bert Address Settings")

    # --- Helper Functions for Bert ---
    def fetch_bert_settings():
        try:
            response = requests.get(f"{get_api_url()}/settings/bert")
            response.raise_for_status()
            st.session_state.bert_settings = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch Bert settings: {e}")
            st.session_state.bert_settings = {"url": ""}

    def save_bert_settings(settings_data):
        try:
            response = requests.post(f"{get_api_url()}/settings/bert", json=settings_data)
            response.raise_for_status()
            st.success("Bert settings saved successfully!")
            return True
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to save Bert settings: {e}")
            return False

    # --- UI for Bert ---
    if not st.session_state.bert_settings:
        fetch_bert_settings()

    with st.form(key="bert_settings_form"):
        st.write("Configure the URL for the Bert service.")
        current_url = st.session_state.bert_settings.get("url", "")
        new_url = st.text_input("Bert URL", value=current_url)
        
        if st.form_submit_button("Save Settings"):
            if new_url != current_url:
                if save_bert_settings({"url": new_url}):
                    fetch_bert_settings()
                    st.rerun()
            else:
                st.info("No changes to save.")

# ======================================================================================
# JIRA SETTINGS TAB
# ======================================================================================
with tab_jira:
    st.header("Jira Connection Settings")

    # --- Helper Functions for Jira ---
    def fetch_jira_settings():
        try:
            response = requests.get(f"{get_api_url()}/settings/jira")
            response.raise_for_status()
            st.session_state.jira_settings = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch Jira settings: {e}")
            st.session_state.jira_settings = {"url": "", "username": "", "password": ""}

    def save_jira_settings(settings_data):
        try:
            response = requests.post(f"{get_api_url()}/settings/jira", json=settings_data)
            response.raise_for_status()
            st.success("Jira settings saved successfully!")
            return True
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to save Jira settings: {e}")
            return False

    # --- UI for Jira ---
    if not st.session_state.jira_settings:
        fetch_jira_settings()

    with st.form(key="jira_settings_form"):
        st.write("Configure the connection details for your Jira instance.")
        current_settings = st.session_state.jira_settings
        url = st.text_input("Jira URL", value=current_settings.get("url", ""))
        username = st.text_input("Username", value=current_settings.get("username", ""))
        password = st.text_input("Password / API Token", type="password", value=current_settings.get("password", ""))
        project = st.text_input("Project", value=current_settings.get("project", ""))
        keywords_str = "\n".join(current_settings.get("keywords", []))
        keywords_text = st.text_area("Keywords (one per line)", value=keywords_str, height=150)

        if st.form_submit_button("Save Settings"):
            keywords_list = [line.strip() for line in keywords_text.split('\n') if line.strip()]
            new_settings = {"url": url, 
                            "username": username, 
                            "password": password, 
                            "project": project,
                            "keywords": keywords_list,
                            }
            if new_settings != current_settings:
                if save_jira_settings(new_settings):
                    fetch_jira_settings()
            else:
                st.info("No changes to save.")

# ======================================================================================
# OLLAMA SETTINGS TAB
# ======================================================================================
with tab_ollama:
    st.header("Ollama Settings")

    # --- Helper Functions for Ollama ---
    def fetch_ollama_settings():
        try:
            response = requests.get(f"{get_api_url()}/settings/ollama")
            response.raise_for_status()
            st.session_state.ollama_settings = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch Ollama settings: {e}")
            st.session_state.ollama_settings = {"url": "", "model": ""}

    def fetch_ollama_models():
        try:
            response = requests.get(f"{get_api_url()}/settings/models")
            response.raise_for_status()
            st.session_state.ollama_models = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch models: {e}")
            st.session_state.ollama_models = []

    def save_ollama_settings(settings_data):
        try:
            response = requests.post(f"{get_api_url()}/settings/ollama", json=settings_data)
            response.raise_for_status()
            st.success("Ollama settings saved successfully!")
            return True
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to save settings: {e}")
            return False

    # --- UI for Ollama ---
    if not st.session_state.ollama_settings:
        fetch_ollama_settings()

    if not st.session_state.ollama_models:
        fetch_ollama_models()

    with st.form(key="ollama_settings_form"):
        st.subheader("Edit Settings")
        current_url = st.session_state.ollama_settings.get("url", "")
        current_model = st.session_state.ollama_settings.get("model", "")
        timeout = st.session_state.ollama_settings.get("timeout", "")
        new_url = st.text_input("Ollama URL", value=current_url)
        timeout_input = st.number_input("timeout", value=timeout)

        model_list = st.session_state.ollama_models
        if current_model and current_model not in model_list:
            model_list = [current_model] + model_list
        index = model_list.index(current_model) if current_model else 0

        selected_model_option = st.selectbox("Change Model", options=model_list, index=index)

        if st.form_submit_button("Save All Settings"):
            final_model = current_model if selected_model_option == "- Do not change -" else selected_model_option
            new_settings = {"url": new_url, "model": final_model, "timeout":timeout_input,}
            if new_settings != st.session_state.ollama_settings:
                if save_ollama_settings(new_settings):
                    fetch_ollama_settings()
            else:
                st.info("No changes to save.")

# ======================================================================================
# LLM MONITORING TAB
# ======================================================================================
with tab_llm:
    st.header("LLM Monitoring Settings")

    # --- Helper Functions for LLM Monitoring ---
    def fetch_llm_monitoring_settings():
        try:
            response = requests.get(f"{get_api_url()}/settings/llm-monitoring")
            response.raise_for_status()
            st.session_state.llm_monitoring_settings = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch LLM Monitoring settings: {e}")
            st.session_state.llm_monitoring_settings = {"webhookUrl": "", "apiKey": "", "monitoringCycle": 10, "analyzedLogPath": "./trace", "analyzedLogMaxNumber": 150}

    def save_llm_monitoring_settings(settings_data):
        try:
            response = requests.post(f"{get_api_url()}/settings/llm-monitoring", json=settings_data)
            response.raise_for_status()
            st.success("LLM Monitoring settings saved successfully!")
            return True
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to save LLM Monitoring settings: {e}")
            return False

    # --- UI for LLM Monitoring ---
    if not st.session_state.llm_monitoring_settings:
        fetch_llm_monitoring_settings()

    with st.form(key="llm_monitoring_form"):
        st.write("Configure the settings for LLM Monitoring.")
        current_settings = st.session_state.llm_monitoring_settings
        webhook_url = st.text_input("Webhook URL", value=current_settings.get("webhookUrl", ""))
        api_key = st.text_input("API Key", type="password", value=current_settings.get("apiKey", ""))
        forward_url = st.text_input("Forward URL", value=current_settings.get("forwardUrl", ""))
        proxy_name = st.text_input("Proxy name", value=current_settings.get("proxyName", ""))
        proxy_passwd = st.text_input("Proxy passwd",  type="password", value=current_settings.get("proxyPasswd", ""))
        analyzed_log_path = st.text_input("Log Path", value=current_settings.get("analyzedLogPath", ""))
        log_max_number = st.number_input("Max Log Number", value=current_settings.get("analyzedLogMaxNumber", 150))
        monitoring_cycle = st.number_input("Monitoring Cycle (e.g., 5m, 1h)", value=current_settings.get("monitoringCycle", 1))
        pending = st.number_input(
            "Pending Timeout (minutes)", 
            min_value=1, 
            value=current_settings.get("pending_timeout_hours", 30),
            help="Hours a task can be in 'Pending' status before being flagged."
        )
        bert = st.number_input(
            "BERT Timeout (minutes)", 
            min_value=1, 
            value=current_settings.get("bert_timeout_minutes", 2),
            help="Minutes a task can be stuck in BERT analysis."
        )
        llm = st.number_input(
            "LLM Timeout (minutes)", 
            min_value=1, 
            value=current_settings.get("llm_timeout_minutes", 30),
            help="Minutes a task can be stuck in LLM analysis."
        )
        tool = st.number_input(
            "Tool Timeout (minutes)", 
            min_value=1, 
            value=current_settings.get("tool_timeout_minutes", 30),
            help="Minutes a task can be stuck in Tool analysis."
        )

        if st.form_submit_button("Save Settings"):
            new_settings = {"webhookUrl": webhook_url,
                            "apiKey": api_key,
                            "forwardUrl": forward_url,
                            "proxyName": proxy_name,
                            "proxyPasswd": proxy_passwd,
                            "analyzedLogPath": analyzed_log_path,
                            "analyzedLogMaxNumber": log_max_number,
                            "monitoringCycle": monitoring_cycle,
                            "pendingTimeout": pending,
                            "bertTimeout": bert,
                            "llmTimeout": llm,
                            "toolTimeout": tool
                }
            if new_settings != current_settings:
                if save_llm_monitoring_settings(new_settings):
                    fetch_llm_monitoring_settings()
            else:
                st.info("No changes were made.")


# ======================================================================================
# SAMBA SETTINGS TAB
# ======================================================================================
with tab_samba:
    st.header("Samba Server Settings")

    # --- Helper Functions for Samba ---
    def fetch_samba_settings():
        try:
            response = requests.get(f"{get_api_url()}/settings/samba")
            response.raise_for_status()
            servers = response.json()
            # Ensure each server has a unique client-side ID
            for server in servers:
                if 'id' not in server:
                    server['id'] = str(uuid4())
            st.session_state.samba_settings = servers
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch Samba servers: {e}")
            st.session_state.samba_settings = []

    def save_all_samba_settings(servers):
        try:
            response = requests.post(f"{get_api_url()}/settings/samba", json=servers)
            response.raise_for_status()
            st.success("Samba servers saved successfully!")
            return True
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to save Samba servers: {e}")
            return False

    # --- Dialogs for Samba ---
    @st.dialog("Samba Server Details")
    def samba_server_dialog(server_id=None):
        is_new = server_id is None
        server_data = next((s for s in st.session_state.samba_settings if s['id'] == server_id), None) if not is_new else {"address": "", "username": "", "password": ""}

        with st.form("samba_form"):
            address = st.text_input("Samba Address (e.g., //server/share)", value=server_data.get("address", ""))
            username = st.text_input("Username", value=server_data.get("username", ""))
            password = st.text_input("Password", type="password", value=server_data.get("password", ""))
            
            if st.form_submit_button("Save"):
                updated_server = {"address": address, "username": username, "password": password}
                if is_new:
                    updated_server['id'] = str(uuid4())
                    st.session_state.samba_settings.append(updated_server)
                else:
                    index = next((i for i, s in enumerate(st.session_state.samba_settings) if s['id'] == server_id), -1)
                    if index != -1:
                        st.session_state.samba_settings[index].update(updated_server)
                st.rerun()

    @st.dialog("Confirm Samba Server Deletion")
    def delete_samba_dialog(server_id):
        server_data = next((s for s in st.session_state.samba_settings if s['id'] == server_id), None)
        st.write(f"Are you sure you want to delete the server **'{server_data.get('address')}'**?")
        
        if st.button("Yes, Delete", type="primary"):
            st.session_state.samba_settings = [s for s in st.session_state.samba_settings if s['id'] != server_id]
            st.rerun()

    # --- UI for Samba ---
    if not st.session_state.samba_settings:
        fetch_samba_settings()

    if st.button("Add New Samba Server", type="secondary"):
        samba_server_dialog()

    st.divider()

    if not st.session_state.samba_settings:
        st.info("No Samba servers configured yet. Add one to get started.")
    else:
        for server in st.session_state.samba_settings:
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.write(f"**{server.get('address', 'No Address')}**")
                st.caption(f"Username: {server.get('username', 'N/A')}")
            with col2:
                if st.button("Edit", key=f"edit_samba_{server['id']}", use_container_width=True):
                    samba_server_dialog(server['id'])
            with col3:
                if st.button("Delete", key=f"delete_samba_{server['id']}", type="primary", use_container_width=True):
                    delete_samba_dialog(server['id'])
    
    st.divider()
    if st.button("Save All Samba Changes to Backend", type="primary"):
        if save_all_samba_settings(st.session_state.samba_settings):
            fetch_samba_settings()

# ======================================================================================
# SYSTEM TAB
# ======================================================================================
with tab_system:
    st.header("System Control")
    st.subheader("Restart Backend Server")
    st.write("Trigger a restart of the backend server. This is useful if you have made configuration changes that require a restart to take effect.")

    if st.button("Restart Backend Server", type="primary"):
        with st.spinner("Sending restart command..."):
            try:
                response = requests.post(f"{get_api_url()}/system/restart")
                if response.status_code == 200:
                    st.success("Restart command sent successfully! The server may be temporarily unavailable.")
                else:
                    st.error(f"Failed to restart server. Status code: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to the backend: {e}")
    st.info("Please note: The Streamlit frontend does not automatically reload after a backend restart.")
