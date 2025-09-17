pipeline {
    agent none
    environment {
    WORKSPACE_DIR = "/home/jenkins/workspace/Taxonomy_NEW"
    DB_PATH       = "/home/jenkins/workspace/Taxonomy_NEW/output/metadata.db"
    GRAFANA_FORENSIC_DIR = "/var/lib/grafana/forensic"
    WORKSPACE_DIR = "/data/logs"        
    FORENSIC_AGENT = "/home/jenkins/forensic/collect_agent.py"
    LOKI_URL = "http://loki:3100/loki/api/v1/push"
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





pipeline {
    agent any
    environment {
        WORKSPACE_DIR = "/data/logs"
        FORENSIC_AGENT = "/home/jenkins/forensic/collect_agent.py"
        LOKI_URL = "http://loki:3100/loki/api/v1/push"
        MONGO_URI = credentials('mongo-atlas-secret') // Jenkins credential ID
    }
    stages {
        stage('Stage 1: Initialize') {
        stage('Stage 2: Collect Artifacts') {
        stage('Stage 3: Prioritize Artifacts') {
        stage('Stage 4: Format Logs for Loki') {
            steps {
                sh """
                    echo "[+] Formatting logs for Loki"
                    python3 scripts/format_for_loki.py --in ${WORKSPACE_DIR}/priority.json --out ${WORKSPACE_DIR}/loki_payload.json
                """
            }
        }

        stage('Stage 5: Push Logs to Loki') {
            steps {
                sh """
                    echo "[+] Sending logs to Loki API"
                    curl -X POST -H "Content-Type: application/json" \\
                        -d @${WORKSPACE_DIR}/loki_payload.json ${LOKI_URL}
                """
            }
        }

        stage('Stage 6: Store Metadata in MongoDB Atlas') {
            steps {
                sh """
                    echo "[+] Storing metadata into MongoDB Atlas"
                    python3 scripts/store_metadata.py \\
                        --mongo-uri "${MONGO_URI}" \\
                        --in ${WORKSPACE_DIR}/priority.json
                """
            }
        }

        stage('Stage 7: Visualization') {
            steps {
                sh """
                    echo "[+] Visualization available in Grafana + Loki dashboards"
                    echo "[+] MongoDB Atlas can be queried for metadata insights"
                """
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: "${WORKSPACE_DIR}/*.json", fingerprint: true
        }
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
      }
    }  
    stage('Archive artifacts') {
      agent { label 'agent' }  
      steps {
        stash name: 'artifacts', includes: 'output/**'
        //archiveArtifacts artifacts: 'output/**', fingerprint: true
      }
    }
    stage('Copy artifacts to Master') {
      agent { label 'master' }  
      steps {
        unstash 'artifacts'
        archiveArtifacts artifacts: 'output/**', fingerprint: true
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
