pipeline {
    agent any
    parameters {
         string(name: 'TARGET_IP', defaultValue: '172.16.0.5', description: 'Target VM IP address')
         string(name: 'SSH_CRED_ID', defaultValue: 'target-vm-ssh-key', description: 'Jenkins credential ID for SSH key')
      }
    environment {
        WORKSPACE_DIR = "${env.WORKSPACE}/forensic_workspace"
        DB_PATH = "${env.WORKSPACE}/forensic_workspace/metadata.db"
        TARGET_IP   = "${params.TARGET_IP}"
        SSH_CRED_ID = "${params.SSH_CRED_ID}"
    }
    stages {
        stage('Initialize') {
            steps {
                echo 'Preparing workspace...'
                sh 'mkdir -p ${WORKSPACE_DIR}'
                sh 'python3 scripts/initialize.py --workspace ${WORKSPACE_DIR}'
            }
        }
    stage('Run Agent on Target (collect live data)') {
        steps {
            withCredentials([sshUserPrivateKey(credentialsId: "${SSH_CRED_ID}", keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
                sh '''
                    echo "Running agent remotely..."
                    ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@${TARGET_IP} "python3 /home/$SSH_USER/forensic/collect_agent.py --out /tmp/artifacts.json"
                    echo "Copying artifacts back to controller workspace..."
                    scp -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@${TARGET_IP}:/tmp/artifacts.json ${WORKSPACE_DIR}/artifacts.json
                '''
            }
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
