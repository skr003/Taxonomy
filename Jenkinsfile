// Declarative Jenkinsfile for orchestrating the Python-based forensic pipeline
pipeline {
    agent any
    environment {
        WORKSPACE_DIR = "${env.WORKSPACE}/forensic_workspace"
        DB_PATH = "${env.WORKSPACE}/forensic_workspace/metadata.db"
    }
    stages {
        stage('Initialize') {
            steps {
                echo 'Preparing workspace...'
                sh 'mkdir -p ${WORKSPACE_DIR}'
                sh 'python3 scripts/initialize.py --workspace ${WORKSPACE_DIR}'
            }
        }
        stage('Collect Artifacts') {
            steps {
                echo 'Running Python agent to collect artifacts (simulated)...'
                sh 'python3 scripts/collect_agent.py --input sample_data/sample_input.json --out ${WORKSPACE_DIR}/artifacts.json'
            }
        }
        stage('Prioritize Artifacts') {
            steps {
                echo 'Prioritizing artifacts...'
                sh 'python3 scripts/prioritize.py --in ${WORKSPACE_DIR}/artifacts.json --out ${WORKSPACE_DIR}/priority_list.json'
            }
        }
        stage('Format Logs') {
            steps {
                echo 'Formatting logs to standardized JSON...'
                sh 'python3 scripts/format_json.py --in ${WORKSPACE_DIR}/artifacts.json --out ${WORKSPACE_DIR}/formatted_logs.json'
            }
        }
        stage('Store Metadata') {
            steps {
                echo 'Storing metadata into SQLite DB...'
                sh 'python3 scripts/store_metadata.py --db ${DB_PATH} --meta ${WORKSPACE_DIR}/priority_list.json'
            }
        }
        stage('Push to Grafana') {
            steps {
                echo 'Pushing formatted logs to Grafana (simulated)...'
                sh 'python3 scripts/push_grafana.py --in ${WORKSPACE_DIR}/formatted_logs.json --out ${WORKSPACE_DIR}/grafana_payload.json'
            }
        }
        stage('Notify') {
            steps {
                echo 'Pipeline finished. Artifacts and payloads available in workspace.'
                sh 'ls -l ${WORKSPACE_DIR} || true'
            }
        }
    }
}
