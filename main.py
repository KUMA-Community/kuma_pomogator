import gradio as gr
import requests
import csv
import tempfile
from time import strftime
from pathlib import Path
import json


requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

CSS = """
.toast-wrap.svelte-pu0yf1 {
    background: #FFFFFF !important;
    color: white !important;
}
"""


class Kuma:
    
    def __init__(self):
        
        self.api_version = '/api/v3'
        self.verifiy = False
        self.limit = 250
        self.OK =  'OK'
        self.ERROR = 'ERROR'        
           
    def connect(self, address, port, token):
        
        self.address = address
        self.port = port
        self.token = token
        self.headers = {"Authorization" : "Bearer " + self.token}
        self.base_url = 'https://' + self.address + ':' + self.port + self.api_version
        self.whoami_url = self.base_url + '/users/whoami'

        method = 'get'
        result, r = self._make_request(method=method, url=self.whoami_url)

        return result
  
    def get_correlators(self):
        
        correlators = []
        params = {"kind": "correlator"}
        page = 1
        count = self.limit
        method = 'get'
        services_url = self.base_url + '/services'

        while count == self.limit:
            params['page'] = page
            result, r = self._make_request(method=method, url=services_url, params=params)
            if result['status'] == self.OK:
                for correlator in r.json():
                    correlators.append(
                                        (correlator['name']+';'+ correlator['tenantName'], correlator['resourceID'])
                                        )
                count = len(r.json())
                page = page + 1
            else:
                count = 0
            return result, correlators

    def get_rules_from_correlator(self, correlator_id):

        rules = []
        correlator_url = self.base_url + '/resources/correlator/' + correlator_id
        method = 'get'
            
        result, r = self._make_request(method=method, url=correlator_url)
        
        if result['status'] == self.OK:
            for rule in r.json()['payload']['rules']:
                rules.append([rule['name'], rule['kind'],  rule['id']])
 
        return result, rules

    def get_rules_from_tenant(self, tenant_id):
        rules = []
        page = 1
        count = self.limit

        method = 'get'
        resources_url = self.base_url + "/resources"
        params = {
            "kind": "correlationRule",
            "tenantID": tenant_id
        }

        while count == self.limit:
            
            params['page'] = page
            
            result, r = self._make_request(method=method, url=resources_url, params=params)

            if result['status'] == self.OK:
                rules_batch = r.json()
                for r in rules_batch:                  
                    rules.append(
                        [r['name'], r['kind'],  r['id']]
                    )  
                count = len(rules_batch)
                page = page + 1
            else:
                count = 0

        return result, rules

    def get_alerts_list(self, status=None, time_field=None, start=None, end=None):

        if start:
            start = start.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        if end:
            end = end.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        alerts = []
        page = 1
        count = self.limit
        alerts_url = self.base_url + '/alerts'
        params = {
            "timestampField": time_field,
            "from": start,
            "to": end,
            "status": status
        }
        method = 'get'
        
        while count == self.limit:
            params['page'] = page
            result, r = self._make_request(method=method, url=alerts_url, params=params)
            if result['status'] == self.OK:
                alerts_batch = r.json()
                for a in alerts_batch:
                    alerts.append(
                        [a['name'], a['id'], a['status'], a['firstSeen'], a['lastSeen'], a['assignee'], a['tenantName'], a['tenantID']]
                    )
                count = len(alerts_batch)
                page = page + 1
            else:
                count = 0

        return result, alerts

    def get_incidents_list(self, status=None, time_field=None, start=None, end=None):
        
        if start:
            start = start.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        if end:
            end = end.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        incidents = []
        page = 1
        count = self.limit
        incidents_url = self.base_url + '/incidents'
        params = {
            "timestampField": time_field,
            "from": start,
            "to": end,
            "status": status
        }
        method = 'get'

        while count == self.limit:
            params['page'] = page
            result, r = self._make_request(method=method, url=incidents_url, params=params)
            if result['status'] == self.OK:
                incidents_batch = r.json()['incidents']
                for i in incidents_batch:
                    incidents.append(
                        [i['name'], i['id'], i['status'], i['createdAt'], i['updatedAt'], i['assigneeName'], i['tenantName'], i['tenantID']]
                    )
                count = len(incidents_batch)
                page = page + 1
            else:
                count = 0
        return result, incidents

    def backup(self):

        backup_url = self.base_url + '/system/backup'
        backup_file = None
        method='get'
        result, r = self._make_request(method=method, url=backup_url)

        if result['status'] == self.OK:
            backup_file = r.content

        return result, backup_file    
   
    def restore(self, file):
        
        restore_url = self.base_url + '/system/restore'
        method = 'post'
        result, r = self._make_request(method=method, url=restore_url, data=file)
        
        return result
    
    def get_resources_list(self, kind=None, name=None):

        resources = []
        page = 1
        count = self.limit

        method = 'get'
        resources_url = self.base_url + "/resources"
        params = {
            "kind": kind,
            "name": name
        }

        while count == self.limit:
            
            params['page'] = page
            
            result, r = self._make_request(method=method, url=resources_url, params=params)

            if result['status'] == self.OK:
                resources_batch = r.json()
                for r in resources_batch:                  
                    resources.append(
                        (r['name'] + '; ' + r['tenantName'], r['kind'] + ';' + r['id'])
                    )  
                count = len(resources_batch)
                page = page + 1
            else:
                count = 0

        return result, resources
    
    def get_resource(self, kind, id):       
        
        resource = {}
        resource_url  = self.base_url + f'/resources/{kind}/{id}'
        method = 'get'
        result, r = self._make_request(method=method, url=resource_url)
        
        if result['status'] == self.OK:
            resource = r.json()
        
        return result, resource
    
    def import_assets(self, assets, tenant_id):

        assets_url = self.base_url + "/assets/import"
        params = {
            "assets": assets,
            "tenantID": tenant_id
        }
        method='post'

        result, r = self._make_request(method=method, url=assets_url, data=json.dumps(params))

        return result
    
    def get_tenants(self):

        tenants = []
        page = 1
        count = self.limit
        
        method = 'get'
        tenants_url = self.base_url + "/tenants"
        params = {}

        while count == self.limit:
            params['page'] = page
            result, r = self._make_request(method=method, url=tenants_url, params=params)
            
            if result['status'] == self.OK:
                tenants_batch = r.json()
                for t in tenants_batch:
                    tenants.append(
                        (t['name'], t['id'])
                    )
                count = len(tenants_batch)
                page = page + 1
            
            else:
                count = 0
        
        return result, tenants

    def _make_request(self, method, url, params=None, data=None):
        
        result = {
                    "status": None,
                    "details": None
                  }
        try:
            r = requests.request(method=method, url=url, params=params, data=data, verify=self.verifiy, headers=self.headers)
            if r.status_code == 200 or r.status_code == 204:
                result['status'] = self.OK
                result['details'] = ''
            else:
                result['status'] = self.ERROR
                result['details'] = f"Status code: {r.status_code}. Details: {r.text}"
        
        except Exception as e:
            result['status'] = self.ERROR
            result['details'] = str(e)
        
        finally:
            return result, r
            
            
def init_tabs(address, port, token):
    result = new_kuma.connect(address, port, token)
    if result['status'] == new_kuma.OK:
        gr.Info("Connection successful", duration=3)
        return gr.Tab(visible=True), gr.Tab(visible=True), gr.Tab(visible=True), gr.Tab(visible=True), "Status: **Connected**"
    else:
        return gr.Tab(visible=False), gr.Tab(visible=False), gr.Tab(visible=False), gr.Tab(visible=False), "Status: **Not connected**"


def get_alerts_csv(status, time_field, start, end):
    
    result, alerts = new_kuma.get_alerts_list(status, time_field, start, end)
    temp_path = None
    
    if result['status'] == new_kuma.OK:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        temp_path = temp_file.name
        
        with open(temp_path, 'w', newline='', encoding='utf8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['name', 'id', 'status', 'first_seen','last_seen', 'assignee', 'tenantName', 'tenantID'])
            
            for a in alerts:
                writer.writerow(a)
    else:
        raise gr.Error(result['details'])
    
    return temp_path


def get_incidents_csv(status, time_field, start, end):
    
    result, incidents = new_kuma.get_incidents_list(status, time_field, start, end)
    temp_file = None
    
    if result['status'] == new_kuma.OK:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        temp_path = temp_file.name
        
        with open(temp_path, 'w', newline='', encoding='utf8') as csvfile:
            
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['name', 'id', 'status', 'first_seen','last_seen', 'assignee', 'tenantName', 'tenantID'])
            
            for i in incidents:
            
                writer.writerow(i)
    else:
        raise gr.Error(result['details'])
    
    return temp_path


def get_rules_csv(choice, correlator_id, tenant_id):
    
    download_path = None
    
    if choice == 'By tenant':
        result, rules = new_kuma.get_rules_from_tenant(tenant_id)
        if result['status'] == new_kuma.OK:
            download_path = convert_rules_to_csv(rules)
        else:
            raise gr.Error(result['details'])
    else:
        result, rules = new_kuma.get_rules_from_correlator(correlator_id)
        if result['status'] == new_kuma.OK:
            download_path = convert_rules_to_csv(rules)
        else:
            raise gr.Error(result['details'])

    return download_path


def convert_rules_to_csv(rules):
    
    temp_path = None
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_path = temp_file.name

    with open(temp_path, 'w', newline='', encoding='utf8') as csvfile:
        
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['name', 'kind', 'id'])
        
        for r in rules:
            writer.writerow(r)
        
    return temp_path


def get_backup():
    gr.Info("Backup in progress, please wait. It may take up to 5 minutes.")
    result, backup = new_kuma.backup()
    temp_path = None
    if result['status'] == new_kuma.OK:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz")
        temp_path = temp_file.name
        with open(temp_path, 'wb') as file:
            file.write(backup)
    
    else:
        raise gr.Error(result['details'])
    
    return temp_path


def restore_backup(file):

    with open(file, 'rb') as f:
        filedata = f.read()
    
    result = new_kuma.restore(filedata)
    if result['status'] == new_kuma.OK:
        gr.Info("Backup successfuly scheduled")
    else:
        raise gr.Error(result['details'])


def search_resources(kind, name):
    
    result, resources = new_kuma.get_resources_list(kind, name)

    if result['status'] == new_kuma.OK:
        return gr.Dropdown(interactive=True, choices=resources, value=None)
    else:
        raise gr.Error(result['details'])
        return None
    
    
def get_resource_json(kind_and_id):
    kind, id = kind_and_id.split(';')
    result, resource = new_kuma.get_resource(kind, id)
    if result['status'] != new_kuma.OK:
        raise gr.Error(result['details'])
    return resource


def import_assets_from_csv(assets_in_csv, tenant_id):
    
    assets = []
    try:
        with open(assets_in_csv, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                assets.append(
                    {
                        "name": row['name'],
                        "fqdn": row['fqdn'].split(';') if len(row['fqdn']) > 0 else [],
                        "ipAddresses": row['ipAddresses'].split(';') if len(row['ipAddresses']) > 0 else [],
                        "macAddresses": row['macAddresses'].split(';') if len(row['macAddresses']) > 0 else [],
                        "os": {
                            "name": row['osName'],
                            "version": int(row['osVersion'])
                        }

                    }
                )

    except Exception as e:
        raise gr.Error(str(e))
   
    result = new_kuma.import_assets(assets, tenant_id)

    if result['status'] == new_kuma.OK:
        gr.Info("Assets has been imported. Details: " + result['details'])
    else:
        raise gr.Error(result['details'])


def prepare_tenants_dd():
    result, tenants = new_kuma.get_tenants()
    if result['status'] == new_kuma.OK:
        return gr.Dropdown(visible=True, choices=tenants, value=None, label="Choose tenant")
    else:
        raise gr.Error(result['details'])
        return None


def prepare_tenants_and_correlators_dd(choice):
    
    if choice == "By tenant":
        result, tenants = new_kuma.get_tenants()
        if result['status'] != new_kuma.OK:
            raise gr.Error(result['details'])
        return gr.Dropdown(visible=False), gr.Dropdown(visible=True, value=None, choices=tenants)

    else:
        result, correlators = new_kuma.get_correlators()
        if result['status'] != new_kuma.OK:
            raise gr.Error(result['details'])
        return gr.Dropdown(visible=True, value=None, choices=correlators), gr.Dropdown(visible=False)


new_kuma = Kuma()

with gr.Blocks(theme=gr.themes.Ocean(), css=CSS) as block_main:
    
    gr.Markdown("# KUMA's User Assistant")

    # LOGIN
    with gr.Row():

        #TODO: change delete password and values!!!
        address = gr.Textbox(show_label=False, placeholder="KUMA Core address", interactive=True)
        port = gr.Textbox('7223', show_label=False, placeholder="KUMA API port", interactive=True)
        token = gr.Textbox(show_label=False, placeholder="KUMA API Token", type='password', interactive=True)
        
        with gr.Column():

            connect = gr.Button("Connect to KUMA")
            connection_status = gr.Markdown("Status: **Not connected**")
        
    # HOME TAB
    with gr.Tab("Home", visible=True, elem_id='home_tab') as home_tab:
        home_md = gr.Markdown('''## Добро пожаловать в KUMA's User Assistant!
                    
                    Данный инструмент предназначен для помощи пользователям KUMA.

                    Для того, чтобы начать, введите в поля выше адрес, порт, а также API-токен и нажмите кнопку Connect to KUMA.

                    Если вы все сделали правильно, вы увидите дополнительные вкладки:

                    **Export** - позволит экспортировать алерты, инциденты или правила корреляции в формате CSV

                    **Assets** - позволит импортировать активы в формате CSV

                    **Backup/Restore** - позволит выполнить резервное копирование и восстановление KUMA

                    **Ananlyze** - позволит проанализировать в формате JSON любой ресурс KUMA
                        ''')
    
    # EXPORT OT CSV ALERTS/INCIDENTS/RULES
    with gr.Tab("Export", visible=False, elem_id='export_tab') as export_tab:
        with gr.Row():

            # ALERTS
            with gr.Column():

                gr.Markdown("### Alerts")
                alert_status = gr.CheckboxGroup(["new", "assigned", "closed", "escalated"], 
                                                label="Status", 
                                                info="Check alert status to export", 
                                                interactive=True, 
                                                value=["new", "assigned", "closed", "escalated"])
                
                with gr.Accordion("Timestamp (optional)", open=False):
                    with gr.Column():
                        alert_time_field = gr.Dropdown(["firstSeen", "lastSeen"], value=None, label="Timestamp field")
                        with gr.Row():
                            alert_start = gr.DateTime(label="From", type='datetime')
                            alert_end = gr.DateTime(label="To", type='datetime')

                export_alerts = gr.Button("Export alerts to CSV")
                export_alerts_hidden = gr.DownloadButton(visible=False, 
                                                         elem_id='export_alerts_hidden')

                export_alerts.click(fn=get_alerts_csv, 
                                    inputs=[alert_status, alert_time_field, alert_start, alert_end], 
                                    outputs=export_alerts_hidden).then(fn=None, 
                                                                       inputs=None, 
                                                                       outputs=None, 
                                                                       js="() => document.querySelector('#export_alerts_hidden').click()")

            # INCIDENTS
            with gr.Column():
                
                gr.Markdown("### Incidents")
                incident_status = gr.CheckboxGroup(["open", "assigned", "closed"], 
                                 label="Status",
                                 info="Check incident status to export", 
                                 interactive=True,
                                 value=["open", "assigned", "closed"])
                
                with gr.Accordion("Timestamp (optional)", open=False):
                    
                    with gr.Column():
                        incident_time_field = gr.Dropdown(["createdAt", "updatedAt"], value=None, label="Timestamp field")
                        with gr.Row():
                            incident_start = gr.DateTime(label="From", type='datetime')
                            incident_end = gr.DateTime(label="To", type='datetime')

                export_incidents = gr.Button("Export incidents to CSV")
                export_incidents_hidden = gr.DownloadButton(visible=False, 
                                                         elem_id='export_incidents_hidden')

                export_incidents.click(fn=get_incidents_csv, 
                                    inputs=[incident_status, incident_time_field, incident_start, incident_end], 
                                    outputs=export_incidents_hidden).then(fn=None, 
                                                                       inputs=None, 
                                                                       outputs=None, 
                                                                       js="() => document.querySelector('#export_incidents_hidden').click()")

            # RULES
            with gr.Column():
                
                gr.Markdown("### Correaltion Rules")
                # get_correlators = gr.Button("Get correlators")

                rules_option = gr.Radio(["By correlator", "By tenant"], value="By correlator", label="Option")
                
                rules_correlators = gr.Dropdown(choices=None, 
                       visible=True, interactive=True, 
                       info="Select correlator", 
                       label="Correlator")
                
                rules_tenants = gr.Dropdown(choices=None, 
                       visible=False, interactive=True, 
                       info="Select tenant", 
                       label="Tenant")

                export_rules = gr.Button("Download rules in CSV", visible=True)
                export_rules_hidden = gr.DownloadButton(visible=False, elem_id='export_rules_hidden')

                export_tab.select(fn=prepare_tenants_and_correlators_dd, inputs=rules_option, outputs=[rules_correlators, rules_tenants])
                rules_option.change(fn=prepare_tenants_and_correlators_dd, inputs=rules_option, outputs=[rules_correlators, rules_tenants])
                export_rules.click(fn=get_rules_csv, 
                                   inputs=[rules_option, rules_correlators, rules_tenants], 
                                   outputs=export_rules_hidden).then(fn=None, 
                                                                     inputs=None, 
                                                                     outputs=None, 
                                                                     js="() => document.querySelector('#export_rules_hidden').click()")
    
    # ASSETS
    with gr.Tab("Assets", visible=False, elem_id="assets_tab") as assets_tab:

        gr.Markdown('''Чтобы импортировать активы, выберите тенант для импорта и загрузите csv-файл с активами.
                    
                    В csv-файле обязательно должен быть заголовок: name,fqdn,ipAddresses,macAddresses,osName,osVersion
                    
                    Для каждого актива должно быть заполнено как минимум одно из двух полей **fqdn** или **ipAddress**
                    
                    Поля **fqdn**, **ipAddresses**, **macAddresses** являются массивами, используйте **;** для разделения значений внутри
                    ''')
        
        # get_tenants = gr.Button("Get tenants")
        assets_tenants = gr.Dropdown(visible=True)
        upload_assets_csv = gr.File(label="Upload CSV", visible=True, interactive=True)
        import_assets = gr.Button("Import assets from CSV", visible=True, interactive=False)

        # get_tenants.click(fn=prepare_tenants_dd, inputs=None, outputs=[tenants])

        assets_tab.select(fn=prepare_tenants_dd, inputs=None, outputs=[assets_tenants])

        upload_assets_csv.change(
            fn=lambda x: gr.Button(interactive=True),
                    inputs=upload_assets_csv,
                    outputs=import_assets
        )

        upload_assets_csv.clear(
            fn=lambda x: gr.Button(interactive=False),
                    inputs=upload_assets_csv,
                    outputs=import_assets
        )

        import_assets.click(fn=import_assets_from_csv, inputs=[upload_assets_csv, assets_tenants], outputs=None)

    # BACKUP/RESTORE
    with gr.Tab("Backup/Restore", visible=False) as backup_tab:
        with gr.Row():
            # BACKUP
            with gr.Column():

                export_backup = gr.Button("Create and download Backup", visible=True)
                export_backup_hidden = gr.DownloadButton(visible=False, elem_id='export_backup_hidden')
                export_backup.click(fn=get_backup, 
                                        inputs=None, 
                                        outputs=export_backup_hidden, api_name="process").then(fn=None, 
                                                                            inputs=None, 
                                                                            outputs=None, 
                                                                            js="() => document.querySelector('#export_backup_hidden').click()")
            # RESTORE
            with gr.Column():
                
                upload_backup = gr.File(label="Upload backup file", type='filepath')
                import_backup = gr.Button("Restore backup", visible=False)

                upload_backup.change(
                    fn=lambda x: gr.Button(visible=True),
                    inputs=upload_backup,
                    outputs=import_backup
                )

                upload_backup.clear(
                    fn=lambda x: gr.Button(visible=False),
                    inputs=upload_backup,
                    outputs=import_backup
                )

                import_backup.click(fn=restore_backup, inputs=[upload_backup], outputs=None)

    # RESOURCE IN JSON ANALYZER
    with gr.Tab("Analyzer", visible=False) as json_tab:
        with gr.Row():
            with gr.Column():
                
                resource_kind = gr.Dropdown(["collector", "correlator", "storage", "activeList", "aggregationRule", "connector", 
                                             "correlationRule", "dictionary", "enrichmentRule", "destination", "filter", "normalizer", 
                                             "responseRule", "search", "agent", "proxy", "secret", "contextTable", "emailTemplate", 
                                             "segmentationRule", "eventRouter"], value=None, label="Select resource kind")
                resource_name = gr.Textbox(placeholder="RE:2 query to search resource", interactive=True)
                search_resource = gr.Button("Search")
                resources_list = gr.Dropdown(label="Chose resource")
                convert_resource_to_json = gr.Button("View resource in JSON")
            
            with gr.Column(scale=3):
                
                resource_json = gr.JSON(show_indices=False)
            
            search_resource.click(fn=search_resources, inputs=[resource_kind, resource_name], outputs=[resources_list])
            convert_resource_to_json.click(fn=get_resource_json, inputs=[resources_list], outputs=[resource_json])

    connect.click(fn=init_tabs, inputs=[address, port, token], outputs=[export_tab, assets_tab, backup_tab, json_tab, connection_status])

    
if __name__ == "__main__":
    block_main.launch()
