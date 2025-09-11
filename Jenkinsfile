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

        stage('Collect Artifacts on Target') {
            agent { label 'target-vm' }   // This runs directly on the Target VM
            steps {
                echo 'Running agent script on target VM...'
                sh 'python3 /opt/forensic/collect_agent.py --input /tmp/sample_input.json --out /tmp/artifacts.json'
            }
        }

        stage('Copy Artifacts Back') {
            agent any
            steps {
                echo 'Copying artifacts from target VM to controller...'
                sh '''
                    scp jenkins@target-vm:/tmp/artifacts.json ${WORKSPACE_DIR}/
                '''
            }
        }

        stage('Prioritize Artifacts') {
            steps {
                sh 'python3 scripts/prioritize.py --in ${WORKSPACE_DIR}/artifacts.json --out ${WORKSPACE_DIR}/priority_list.json'
            }
        }

        stage('Format Logs') {
            steps {
                sh 'python3 scripts/format_json.py --in ${WORKSPACE_DIR}/artifacts.json --out ${WORKSPACE_DIR}/formatted_logs.json'
            }
        }

        stage('Store Metadata') {
            steps {
                sh 'python3 scripts/store_metadata.py --db ${DB_PATH} --meta ${WORKSPACE_DIR}/priority_list.json'
            }
        }

        stage('Push to Grafana (Simulated)') {
            steps {
                sh 'python3 scripts/push_grafana.py --in ${WORKSPACE_DIR}/formatted_logs.json --out ${WORKSPACE_DIR}/grafana_payload.json'
            }
        }

        stage('Notify & Archive') {
            steps {
                echo 'Archiving artifacts...'
                archiveArtifacts artifacts: 'forensic_workspace/**', fingerprint: true
            }
        }
    }
}
