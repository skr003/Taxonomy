pipeline {
    agent none
    environment {
    WORKSPACE_DIR = "/home/jenkins/workspace/Taxonomy_NEW"
    MASTER_WORKSPACE_DIR = "/var/lib/jenkins/workspace/Taxonomy_NEW"
    DB_PATH       = "/home/jenkins/workspace/Taxonomy_NEW/output/metadata.db"
    GRAFANA_FORENSIC_DIR = "/var/lib/grafana/forensic"
    FORENSIC_AGENT = "/home/jenkins/forensic/collect_agent.py"
    LOKI_URL = "http://172.16.0.4:3100/loki/api/v1/push"
    MONGO_URI = credentials('mongo-atlas-secret') // Jenkins credential ID
    }
  stages {
    stage('Deploy Agent Script & Collect Logs') {
      agent { label 'agent' }
      steps {
      sh '''
        chmod -R 700 /home/jenkins/workspace/ || true
        echo "Copying agent to target..."
        scripts/collect_agent.py
      '''
    }
  }
    stage('Prioritize Artifacts') {
      agent { label 'agent' }
      steps {
        sh 'python3 scripts/prioritize.py --in ${WORKSPACE_DIR}/output/artifacts.json --out ${WORKSPACE_DIR}/output/priority_list.json'
      }
    }
    stage('Format and Split Logs') {
        agent { label 'agent' }
        steps {
        sh 'python3 scripts/format_json.py --in ${WORKSPACE_DIR}/output/artifacts.json --out ${WORKSPACE_DIR}/output/formatted_logs.json'
        sh 'python3 scripts/split_formatted_logs.py'
        stash name: 'artifacts', includes: 'output/**'    
      }
    }   
        stage('Format Logs for Loki') {
            agent { label 'master' }  
            steps {
                unstash 'artifacts'
                archiveArtifacts artifacts: 'output/**', fingerprint: true                
                sh """
                    unstash 'artifacts'
                    archiveArtifacts artifacts: 'output/**', fingerprint: true
                    echo "[+] Formatting logs for Loki"
                    python3 scripts/format_for_loki.py --in ${MASTER_WORKSPACE_DIR}/output/priority_list.json --out ${MASTER_WORKSPACE_DIR}/output/loki_payload.json
                """
            }
        }
        stage('Push Logs to Loki') {
            agent { label 'master' }  
            steps {
                sh """
                    echo "[+] Sending logs to Loki API"
                    curl -X POST -H "Content-Type: application/json" \\
                        -d @${MASTER_WORKSPACE_DIR}/output/loki_payload.json ${LOKI_URL}
                """
            }
        }
        stage('Store Metadata in MongoDB Atlas') {
            agent { label 'master' }   
            steps {
                sh """
                    echo "[+] Storing metadata into MongoDB Atlas"
                    python3 scripts/store_metadata.py --mongo-uri "${MONGO_URI}" --in ${MASTER_WORKSPACE_DIR}/output/priority_list.json
                """
            }
        }
        stage('Visualization') {
            agent { label 'master' }  
            steps {
                sh """
                    echo "[+] Visualization available in Grafana + Loki dashboards"
                    echo "[+] MongoDB Atlas can be queried for metadata insights"
                """
            }
        }
    stage('Upload Reports to Azure Storage') {
      agent { label 'master' }    
      steps {
            script {
            withCredentials([
                string(credentialsId: 'TAXONOMY_STORAGE_ACCOUNT_KEY', variable: 'TAXONOMY_STORAGE_ACCOUNT_KEY')
                    ]) {
                sh '''
                # Set variables - REPLACE WITH YOUR ACTUAL STORAGE KEY
                STORAGE_ACCOUNT="taxonomystorage123"
                CONTAINER="reports"
                az storage blob upload-batch --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --destination "reports/builds/$BUILD_NUMBER" --source output --overwrite
                az storage blob upload-batch --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --destination "reports/latest" --source output --overwrite
                '''
            }  
      }
    }        
    }
  }
}
